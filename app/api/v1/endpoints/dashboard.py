import os
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from models.thumbnail import Thumbnail
from db.database import get_db
from utils import get_current_user_id


api_router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@api_router.get("/image/{image_name}")
def get_thumbnail_image(image_name: str, response: Response):
    image_path = f"thumbnails/{image_name}"
    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail="Image not found")
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return FileResponse(image_path, media_type="image/png")


@api_router.get("/thumbnail/{thumbnail_id}")
def get_thumbnail_info(thumbnail_id: int, request: Request, db: Session = Depends(get_db)):
    """Returns the original (un-annotated) thumbnail URL — used by the canvas editor as background."""
    thumbnail = db.query(Thumbnail).filter(Thumbnail.id == thumbnail_id).first()
    if not thumbnail:
        raise HTTPException(status_code=404, detail="Thumbnail not found")
    base_url = str(request.base_url).rstrip("/")
    filename = os.path.basename(thumbnail.thumbnailpath)
    return {
        "id": thumbnail.id,
        "image_url": f"{base_url}/api/v1/dashboard/image/{filename}",
    }


@api_router.get("/")
def get_dashboard_data(
    request: Request,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    try:
        dashboards = (
            db.query(Thumbnail)
            .filter(Thumbnail.userid == user_id)
            .all()
        )

        base_url = str(request.base_url).rstrip("/")
        result = []

        for d in dashboards:
            # Show the annotated canvas PNG if it exists, else the original thumbnail
            canvas_path = f"thumbnails/canvas_{d.id}.png"
            if os.path.exists(canvas_path):
                filename = f"canvas_{d.id}.png"
                source_path = canvas_path
            else:
                filename = os.path.basename(d.thumbnailpath)
                source_path = d.thumbnailpath

            try:
                mtime = int(os.path.getmtime(source_path))
            except OSError:
                mtime = 0

            result.append({
                "id": d.id,
                "image_url": f"{base_url}/api/v1/dashboard/image/{filename}?v={mtime}",
            })

        return {"data": result}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching dashboard data: {str(e)}")
