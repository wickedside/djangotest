import logging
from ninja import NinjaAPI, Router
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from ninja import Schema
from typing import List
from orders.models import Order

logger = logging.getLogger(__name__)

api = NinjaAPI()

@api.get("/test")
def test(request):
    logger.debug("Test endpoint called")
    return {"message": "ok"}

@api.post("/register")
def register(request, username: str, email: str, password: str, category: str):
    logger.debug(f"Register attempt for user: {username}")
    if User.objects.filter(username=username).exists() or User.objects.filter(email=email).exists():
        logger.warning(f"User registration failed for {username}: User already exists")
        return {"error": "User with this username or email already exists"}, 400

    user = User.objects.create(
        username=username,
        email=email,
        password=make_password(password)
    )
    logger.info(f"User {username} registered successfully")

    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }

@api.post("/login")
def login(request, username: str, password: str):
    logger.debug(f"Login attempt for user: {username}")
    user = authenticate(username=username, password=password)
    if user:
        refresh = RefreshToken.for_user(user)
        logger.info(f"User {username} logged in successfully")
        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }
    else:
        logger.warning(f"Login failed for user: {username}")
        return {"error": "Invalid credentials"}, 401

class OrderSchema(Schema):
    title: str
    description: str
    category: str

class OrderCreate(Schema):
    title: str
    description: str
    category: str

@api.post("/orders", response=OrderSchema)
def create_order(request, payload: OrderCreate):
    logger.debug(f"Creating order for user: {request.auth}")
    if not request.auth:
        logger.warning("Order creation failed: Authentication required")
        return {"error": "Authentication required"}, 401

    order = Order.objects.create(
        title=payload.title,
        description=payload.description,
        category=payload.category,
        user=request.auth
    )
    logger.info(f"Order created successfully: {order.title}")
    return order

@api.get("/orders", response=List[OrderSchema])
def list_orders(request):
    logger.debug(f"Listing orders for user: {request.auth}")
    if not request.auth:
        logger.warning("Order listing failed: Authentication required")
        return {"error": "Authentication required"}, 401

    orders = Order.objects.filter(category=request.auth.profile.category)
    logger.info(f"Orders listed successfully for user: {request.auth}")
    return orders