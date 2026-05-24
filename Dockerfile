FROM python:3.10

RUN apt-get update && \
    apt-get install -y ffmpeg nodejs npm && \
    apt-get clean

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -U pip
RUN pip install --no-cache-dir -U -r requirements.txt
RUN pip install youtube-search-python==1.6.6

CMD ["bash", "start"]
