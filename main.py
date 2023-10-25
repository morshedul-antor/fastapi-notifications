from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel
from datetime import datetime
import uvicorn
import uuid

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title='WebSocket Example')

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    # Replace with your frontend's URL
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# SQLAlchemy setup
engine = create_engine("sqlite:///notifications.db")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    message = Column(String)
    created_at = Column(DateTime, default=datetime.now)
    session_id = Column(String)


Base.metadata.create_all(bind=engine)


class UserNotifications(BaseModel):
    session_id: str
    notifications: list


active_connections = {}
permanent_booking_info = []  # A list to store permanent booking info


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    session_id = str(uuid.uuid4())
    active_connections[session_id] = websocket

    try:
        while True:
            message = await websocket.receive_text()
            await websocket.send_text(f"Received: {message}")
    except WebSocketDisconnect:
        del active_connections[session_id]


@app.post('/book-service')
async def book_service(message: str):
    # Logic to book the service
    # ...

    # Store the notification in the database with a session_id
    db = SessionLocal()
    db_notification = Notification(message=message)
    db.add(db_notification)
    db.commit()

    # Store the booking information in the permanent list
    permanent_booking_info.append(message)

    # Broadcast the notification to all connected clients
    for connection in active_connections.values():
        try:
            await connection.send_text(message)
        except WebSocketDisconnect:
            pass

    return "Booked!"


@app.on_event("startup")
async def send_pending_notifications():
    # Send pending notifications to connected clients on startup
    db = SessionLocal()
    notifications = db.query(Notification).all()
    for notification in notifications:
        await send_notification_to_clients(notification.message)


async def send_notification_to_clients(message):
    for connection in active_connections.values():
        try:
            await connection.send_text(message)
        except WebSocketDisconnect:
            pass

# Add the missing API endpoint to fetch permanent booking information


@app.get('/get-permanent-booking-info')
async def get_permanent_booking_info():
    # Query the database for all notifications
    db = SessionLocal()
    notifications = db.query(Notification).all()

    # Create a list to store notifications as dictionaries
    notification_list = []
    for notification in notifications:
        notification_dict = {
            "id": notification.id,
            "message": notification.message,
            "created_at": notification.created_at,
            "session_id": notification.session_id,
        }
        notification_list.append(notification_dict)

    return notification_list


@app.get('/get-total-notifications')
async def get_total_notifications():
    db = SessionLocal()
    notifications = db.query(Notification).all()

    # Create a list to store notifications as dictionaries
    notification_list = []
    for notification in notifications:
        notification_list.append(notification)

    return {"total": len(notification_list)}


if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8000)
