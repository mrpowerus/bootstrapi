FROM python:3.7

ARG connection
ENV connection=$connection

ARG title="BootstrAPI"
ENV title=${title}

ARG host="0.0.0.0"
ENV host=${host}

ARG port=8000
ENV port=${port}

ARG schema
ENV schema=${schema}

COPY . .

RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
RUN curl https://packages.microsoft.com/config/debian/10/prod.list > /etc/apt/sources.list.d/mssql-release.list
RUN apt-get update
RUN ACCEPT_EULA=Y apt-get install -y msodbcsql17
RUN apt-get install -y unixodbc-dev

RUN pip install -r requirements.txt

EXPOSE ${port}

CMD python -m run $connection