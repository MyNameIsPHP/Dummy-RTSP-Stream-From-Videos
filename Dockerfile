FROM ubuntu:22.04

# ENV FPS=30
# ENV IMAGE_WIDTH=400
# ENV IMAGE_HEIGHT=300
# ENV PORT=8554
# ENV URLS=""

WORKDIR /app

COPY stream.py /app

RUN apt-get update -y
RUN apt-get install -y python3 python3-pip gstreamer-1.0 \
                        python3-gst-1.0 gstreamer1.0-plugins-ugly \
                        gir1.2-gst-rtsp-server-1.0 
RUN pip install opencv-python==4.9.0.80 

EXPOSE 8554

CMD ["python3", "stream.py"]
