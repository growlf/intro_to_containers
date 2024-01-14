from pydantic import BaseModel
from sqlmodel import Field, SQLModel, Session, select, create_engine
from fastapi import FastAPI, HTTPException
from faker import Faker
from typing import List, Union

#Define model classes

class OrderBase(BaseModel):
    name: str
    cost: str

class Order(SQLModel, OrderBase, table = True):
    id: int = Field(default = None, primary_key = True)

class CustomerBase(BaseModel):
    name: str
    email: str
    address: str

class Customer(SQLModel, CustomerBase, table = True):
    id: int = Field(default = None, primary_key = True)

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

#Setup App
app = FastAPI()
app.title = "Hello World!"
app.description = "Carpe Diem"

#Define Routes
@app.get("/get-customers/", status_code = 200)
async def get_customers() -> List[Customer]:
    with Session(engine) as sesh:
        sql = select(Customer)
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
