import json
import ssl
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from aiokafka import AIOKafkaProducer
# from conf import KAFKA_BROKERS, KAFKA_TOPIC

app = FastAPI()

KAFKA_BROKERS = 'localhost:9092'
KAFKA_TOPIC = 'search_topic'

class SearchQuery(BaseModel):
    query: str 

class KafkaProducer:
    def __init__(self):
        self.producer: Optional[AIOKafkaProducer] = None

    async def init(self):
        conf = {
            'bootstrap_servers': KAFKA_BROKERS,
        }
        self.producer = AIOKafkaProducer(**conf)
        try:
            await self.producer.start()
        except Exception as e:
            await self.close()
            raise RuntimeError(f"Failed to start Kafka producer: {e}")

    async def close(self):
        if self.producer:
            try:
                await self.producer.stop()
            except Exception as e:
                raise RuntimeError(f"Failed to stop Kafka producer: {e}")

    async def send_search_task(self, search_query):
        message = json.dumps(search_query).encode('utf-8')
        try:
            await self.producer.send_and_wait(KAFKA_TOPIC, message)
            print(f"Sent message: {message}")
        except Exception as e:
            raise RuntimeError(f"Error sending message to Kafka: {e}")

    async def check_health(self):
        if not self.producer or not self.producer._closed:
            return True  
        return False 

kafka_producer = KafkaProducer()

@app.on_event("startup")
async def startup_event():
    await kafka_producer.init()

@app.on_event("shutdown")
async def shutdown_event():
    await kafka_producer.close()

@app.post("/search")
async def search(query: SearchQuery):
    await kafka_producer.send_search_task({"query": query.query})
    return JSONResponse(content={"query": query.query})