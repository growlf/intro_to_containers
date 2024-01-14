from fastapi import FastAPI, HTTPException
from typing import List
from sqlmodel import Field, SQLModel, create_engine, Session

# Define the models
class CustomerBase(SQLModel):
    name: str
    email: str

class Customer(CustomerBase, table=True):
    id: int = Field(default=None, primary_key=True)

class OrderBase(SQLModel):
    customer_id: int
    product: str
    quantity: int

class Order(OrderBase, table=True):
    id: int = Field(default=None, primary_key=True)

# Create the database engine and session
sqlite_url = "sqlite:///./database.db"
engine = create_engine(sqlite_url)
SQLModel.metadata.create_all(engine)
session = Session(engine)

# Create the FastAPI app
app = FastAPI()

# Routes
@app.post("/customers/")
def create_customer(customer: CustomerBase):
    db_customer = Customer.from_orm(customer)
    session.add(db_customer)
    session.commit()
    session.refresh(db_customer)
    return db_customer

@app.get("/customers/", response_model=List[Customer])
def get_customers():
    customers = session.query(Customer).all()
    return customers

@app.get("/customers/{customer_id}", response_model=Customer)
def get_customer(customer_id: int):
    customer = session.query(Customer).get(customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer

@app.put("/customers/{customer_id}", response_model=Customer)
def update_customer(customer_id: int, customer: CustomerBase):
    db_customer = session.query(Customer).get(customer_id)
    if not db_customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    for field, value in customer.dict().items():
        setattr(db_customer, field, value)
    session.add(db_customer)
    session.commit()
    session.refresh(db_customer)
    return db_customer

@app.delete("/customers/{customer_id}")
def delete_customer(customer_id: int):
    db_customer = session.query(Customer).get(customer_id)
    if not db_customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    session.delete(db_customer)
    session.commit()
    return {"message": "Customer deleted"}

# Seed the database with faker objects
from faker import Faker
fake = Faker()

for _ in range(10):
    customer = CustomerBase(name=fake.name(), email=fake.email())
    db_customer = Customer.from_orm(customer)
    session.add(db_customer)
    session.commit()

# Close the session after each request
@app.middleware("http")
async def close_session(request, call_next):
    response = await call_next(request)
    session.remove()
    return response
