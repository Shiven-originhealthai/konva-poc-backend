import base64
import json
import os
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from models.thumbnail import Thumbnail
from models.canvas_state import CanvasState
from db.database import get_db
from utils import get_current_user_id

router = APIRouter(prefix="/canvas", tags=["canvas"])

_NOT_FOUND = "Thumbnail not found"

DB  = Annotated[Session,Depends(get_db)]
Owner= Annotated[int,Depends(get_current_user_id)]


class SaveCanvasRequest(BaseModel):
    canvasUrl:Optional[str] = None  
    thumbnail_id:Optional[int] = None
    lines:Optional[list] = None
    shapes:Optional[list] = None
    text_items:Optional[list] = None

class selectedCanvasImageIdArray(BaseModel):
    selectedCanvasImageIdArray:list[int]


def _decode_base64(data: str) -> bytes:
    raw = data.split(",")[1] if "," in data else data
    return base64.b64decode(raw)


def _upsert_state(db: Session, thumbnail_id: int, user_id: int,
                  lines_j: str, shapes_j: str, text_items_j: str) -> None:
    try:
        existing = (
            db.query(CanvasState)
            .filter(CanvasState.thumbnail_id == thumbnail_id)
            .first()
        )
        if existing:
            existing.lines = lines_j
            existing.shapes = shapes_j
            existing.text_items = text_items_j
            print(f"[canvas] updating state row id={existing.id}")
        else:
            db.add(CanvasState(
                thumbnail_id = thumbnail_id,
                userid = user_id,
                lines  = lines_j,
                shapes = shapes_j,
                text_items = text_items_j,
            ))
            print(f"[canvas] inserting new state row for thumbnail_id={thumbnail_id}")

        db.commit()

        check = db.query(CanvasState).filter(CanvasState.thumbnail_id == thumbnail_id).first()
        if check:
            print(f"[canvas] verified in DB — lines_len={len(check.lines or '')} shapes_len={len(check.shapes or '')}")
        else:
            print("[canvas] row NOT found after commit")

    except Exception as e:
        db.rollback()
        print(f"[canvas] upsert FAILED: {e}")
        raise


def _write_image(path: str, canvas_url: str) -> None:
    os.makedirs("thumbnails", exist_ok=True)
    with open(path, "wb") as f:
        f.write(_decode_base64(canvas_url))


@router.post("/save")
def save_canvas(body: SaveCanvasRequest, user_id: Owner, db: DB):
    try:
        is_edit = body.thumbnail_id is not None

        if is_edit:
            thumbnail = (
                db.query(Thumbnail)
                .filter(Thumbnail.id == body.thumbnail_id, Thumbnail.userid == user_id)
                .first()
            )
            if not thumbnail:
                raise HTTPException(status_code=404, detail=_NOT_FOUND)
            if body.canvasUrl:
                _write_image(thumbnail.thumbnailpath, body.canvasUrl)
        else:
            if not body.canvasUrl:
                raise HTTPException(status_code=400, detail="canvasUrl required for new canvas")
            image_bytes = _decode_base64(body.canvasUrl)
            path = f"thumbnails/thumbnail_{user_id}_{len(image_bytes)}.png"
            os.makedirs("thumbnails", exist_ok=True)
            with open(path, "wb") as f:
                f.write(image_bytes)
            thumbnail = Thumbnail(userid=user_id, thumbnailpath=path)
            db.add(thumbnail)
            db.commit()
            db.refresh(thumbnail)

        _upsert_state(
            db, thumbnail.id, user_id,
            json.dumps(body.lines or []),
            json.dumps(body.shapes or []),
            json.dumps(body.text_items or []),
        )
        msg = "Canvas updated" if is_edit else "Canvas saved"
        return {"success": True, "message": msg, "thumbnail_id": thumbnail.id}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Save failed: {str(e)}")


@router.get("/state/{thumbnail_id}", responses={404: {"description": _NOT_FOUND}})
def get_canvas_state(thumbnail_id: int, user_id: Owner, db: DB):
    """Returns only the annotation state — background image comes from the Card's imageUrl."""
    thumbnail = (
        db.query(Thumbnail)
        .filter(Thumbnail.id == thumbnail_id, Thumbnail.userid == user_id)
        .first()
    )
    if not thumbnail:
        raise HTTPException(status_code=404, detail=_NOT_FOUND)

    row = (
        db.query(CanvasState)
        .filter(CanvasState.thumbnail_id == thumbnail_id)
        .first()
    )
    if not row:
        return {"state": None}

    return {
        "state": {
            "lines": json.loads(row.lines or "[]"),
            "shapes": json.loads(row.shapes or "[]"),
            "textItems":json.loads(row.text_items or "[]"),
        }
    }

@router.post('/delete')
def deleteCanvas(body: selectedCanvasImageIdArray, db: DB):
    selectedArrayIds = body.selectedCanvasImageIdArray

    if not selectedArrayIds:
        raise HTTPException(status_code=400, detail="No IDs provided")

    try:
        db.query(CanvasState).filter(
            CanvasState.thumbnail_id.in_(selectedArrayIds)
        ).delete(synchronize_session=False)

        db.query(Thumbnail).filter(
            Thumbnail.id.in_(selectedArrayIds)
        ).delete(synchronize_session=False)

        db.commit()
        return {"message": f"Deleted {len(selectedArrayIds)} canvas(es) successfully"}

    except HTTPException:
        raise

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete: {str(e)}")


