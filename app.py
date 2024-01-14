from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel
from sqlalchemy.orm import selectinload
from sqlmodel import  SQLModel, Session, select, create_engine
from sqlmodel import Field, Relationship
from fastapi import FastAPI, HTTPException
from faker import Faker
from typing import List, Union

#Define model classes Customer and Order, and their base classes
#Base classes are used for input and output validation
#Model classes are used for database interaction
#Relationships are defined in the model classes

#A customer can have multiple orders

class OrderBase(BaseModel):
    name: str
    cost: Decimal
    customer_id: int
    class Config:
        orm_mode = True

class CustomerBase(BaseModel):
    name: str
    address: str
    email: str
    class Config:
        orm_mode = True

class Customer(CustomerBase, SQLModel, table=True):
    __tablename__ = "customers"
    id: int = Field(default=None, primary_key=True)
    orders: List["Order"] = Relationship(back_populates="customer")

class Order(OrderBase, SQLModel, table=True):
    __tablename__ = "orders"
    id: int = Field(default=None, primary_key=True)
    customer_id: int = Field(default = None, foreign_key="customers.id")
    customer: Customer = Relationship(back_populates="orders")

class CustomerRead(CustomerBase):
    orders: List[Order] = []

#Setup database in memory
sqlite_url = f"sqlite://"
engine = create_engine(sqlite_url, echo=True)
SQLModel.metadata.create_all(engine)

#Sample data
fake = Faker()
with Session(engine) as sesh:
    for customer in (Customer(name = fake.name()
                    ,address = fake.address()
                    ,email = fake.ascii_safe_email())
                    for i in range(10)):
        sesh.add(customer)
    sesh.commit()

with Session(engine) as sesh:
    for customer in sesh.exec(select(Customer)).all():
        for order in (Order(name = fake.text()
                            ,cost = fake.pydecimal(2,2)
                            ,customer_id = customer.id)
                            for i in range(3)):
            sesh.add(order)
    sesh.commit()

#Setup App
app = FastAPI()
app.title = "Hello World!"
app.description = "Carpe Diem"

#Define Routes
@app.get("/get-customers/", status_code = 200)
async def get_customers(offset: int = None, limit: int = None) -> List[Customer]:
    #Use offsets and limits to page through results
    with Session(engine) as sesh:
        offset = offset or 0
        limit = limit or 0
        if limit == 0:
            sql = select(Customer).offset(offset)
        else:
            sql = select(Customer).offset(offset).limit(limit)
        results = sesh.exec(sql).all()
        return results

@app.get("/get-customer-by-id/", status_code = 200)
async def get_customer_by_id(id: int) -> Customer:
    with Session(engine) as sesh:
        customer = sesh.get(Customer, id)
        if customer is not None:
            return customer
        else:
            raise HTTPException(status_code=404, detail = "Customer not found")

@app.post("/create-customer/", status_code = 201)
async def create_customer(base: CustomerBase) -> Customer:
    new_customer = Customer(**base.model_dump())
    with Session(engine) as sesh:
        sesh.add(new_customer)
        sesh.commit()
        sesh.refresh(new_customer)
        return new_customer

@app.put("/update-customer/", status_code = 200)
async def update_customer(customer: Customer) -> Customer:
    with Session(engine) as sesh:
        sesh.merge(customer)
        sesh.commit()
        customer = sesh.get(Customer, customer.id)
        return customer

@app.get("/get-orders/", status_code = 200)
async def get_orders() -> List[Order]:
    with Session(engine) as sesh:
        sql = select(Order)
        results = sesh.exec(sql).all()
        return results
    
@app.get("/get-order-by-id/", status_code = 200)
async def get_order_by_id(id: int) -> Order:
    with Session(engine) as sesh:
        order = sesh.get(Order, id)
        if order is not None:
            return order
        else:
            raise HTTPException(status_code=404, detail = "Order not found")
        
@app.post("/create-order/", status_code = 201)
async def create_order(base: OrderBase) -> Order:
    new_order = Order(**base.model_dump())
    with Session(engine) as sesh:
        sesh.add(new_order)
        sesh.commit()
        sesh.refresh(new_order)
        return new_order
    
@app.put("/update-order/", status_code = 200)
async def update_order(order: Order) -> Order:
    with Session(engine) as sesh:
        sesh.merge(order)
        sesh.commit()
        order = sesh.get(Order, order.id)
        return order
    
@app.get("/get-customer-orders/", status_code = 200)
async def get_customer_orders(id: int) -> List[Order]:
    with Session(engine) as sesh:
        sql = select(Order).where(Order.customer_id == id)
        results = sesh.exec(sql).all()
        return results

@app.get("/get-customer-with-orders/{id}", status_code = 200, response_model=CustomerRead)
async def get_customer_with_orders(id: int) -> CustomerRead:
    with Session(engine) as sesh:
        sql = select(Customer).where(Customer.id == id).options(selectinload(Customer.orders))
        results = sesh.exec(sql).first()
        return results