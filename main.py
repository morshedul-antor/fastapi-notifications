from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import uvicorn


app = FastAPI(title='WebSocket')

# Create a set to store active WebSocket connections
active_connections = set()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.add(websocket)

    try:
        while True:
            message = await websocket.receive_text()
            await websocket.send_text(f"Received: {message}")
    except WebSocketDisconnect:
        active_connections.remove(websocket)
        print("WebSocket client disconnected")


@app.post('/book-service')
async def book_service():
    # Notify all connected clients about the booking
    notification = {'message': 'A new service has been booked!'}
    for connection in active_connections:
        await connection.send_text(notification)
    return "Booked!"

if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8000)
