import sys
import os
import re
import base64
import html

sys.path.insert(0, os.path.abspath("backend"))

from app.services.news_service import unwrap_google_news_url

test_url = "https://news.google.com/rss/articles/CBMizgFBVV95cUxNYUN4enZMbkJ0elBseUsyOHVNVFFoa21GbmZvWHMyZnVDcVh1dzRISUQtcHdYQjM1VnlzdmozMkE5Tzg5ZjFYek1rc1NUcUo5MThwRmRZOWQ5NnhFcVA2Zl9YOE14M1pqZDZ4b3dkVEh1YUhVdkFua3l6RlE0Q1Zidm16el91UnZQTTUyTUtJUXZNUUg0Z1lpSndIU2l3bTBMdTlSem45dzN0VllQUTh1cFludDFZR0toUzZLSlRaQ08wVWs0T19EYThEVkQ5Z9IB2wFBVV95cUxPQ09uOC1DRzVOcGdyQVlOc29Wb3JsNzR4M2dUQU9VQ3JCdXVPSTFVY25FeEhtc2VTbTBEa2ZYc3VlX2ZaYWF5MGc3bEpYcTJRN2xGMWpBTFBNbnB3VDUtejNBYS1BazRlUkg3NVplb2lrS2xvUmhnMEZMby0xWEpsX2t6bDBzZnRpVGJhaU9hS25GdVNlZ1BWWGtkZXBVV2hZMWVqTzBjVUVYZEhGSEdDaXdkN1RySEpMQkdWeDB1dmlkcFRPVUFoYzl3TTBmamlJaXd3bGd4OTNCalk?oc=5"

unwrapped = unwrap_google_news_url(test_url)
print("=========================================================")
print(f"Original Google RSS URL: {test_url[:60]}...")
print(f"Unwrapped Destination URL: {unwrapped}")
print("=========================================================")
