"""Pedidos demonstrativos. Não há processamento de pagamento."""
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.security import get_current_user, get_optional_user
from app.database.connection import get_db
from app.database.models import Order, OrderItem, User
from app.schemas import OrderIn, OrderOut
from app.services.catalog import products_by_id

router = APIRouter(prefix="/api/orders", tags=["Pedidos"])


def _out(order: Order) -> OrderOut:
    return OrderOut(id=order.id, status=order.status, total=order.total, created_at=order.created_at,
                    is_guest=order.user_id is None, items=order.items)


@router.post("", response_model=OrderOut, status_code=status.HTTP_201_CREATED,
             summary="Finaliza um pedido demonstrativo (com ou sem login)")
def create_order(body: OrderIn, db: Session = Depends(get_db), user: User | None = Depends(get_optional_user)):
    # Agrega itens repetidos e usa SEMPRE o preço do banco (nunca o do cliente).
    qty: dict[str, int] = {}
    from_rec: dict[str, bool] = {}
    for item in body.items:
        qty[item.product_id] = qty.get(item.product_id, 0) + item.quantity
        from_rec[item.product_id] = from_rec.get(item.product_id, False) or item.from_recommendation
    products = products_by_id(db, set(qty))
    missing = sorted(set(qty) - set(products))
    if missing:
        raise HTTPException(422, f"Produtos inexistentes: {', '.join(missing)}")

    order = Order(
        user_id=user.id if user else None,
        guest_label=None if user else (body.guest_label or None),
        status="demo_confirmed",
        total=Decimal("0"),
    )
    for pid, q in qty.items():
        order.items.append(OrderItem(product_id=pid, quantity=q, unit_price=products[pid].price,
                                     from_recommendation=from_rec[pid]))
    order.total = sum((i.unit_price * i.quantity for i in order.items), Decimal("0"))
    db.add(order)
    db.commit()
    db.refresh(order)
    return _out(order)


@router.get("/me", response_model=list[OrderOut], summary="Pedidos do usuário autenticado")
def my_orders(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    orders = db.scalars(select(Order).where(Order.user_id == user.id)
                        .options(selectinload(Order.items)).order_by(Order.created_at.desc())).all()
    return [_out(o) for o in orders]


@router.get("/{order_id}", response_model=OrderOut, summary="Pedido do próprio usuário")
def get_order(order_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    order = db.get(Order, order_id)
    # 404 também para pedidos de outros usuários: não revela a existência.
    if order is None or order.user_id != user.id:
        raise HTTPException(404, "Pedido não encontrado.")
    return _out(order)
