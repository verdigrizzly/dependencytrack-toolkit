FROM python:3.13-alpine
ARG BUILD_ENV
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
ENV ca_path=/etc/ssl/certs/ca-certificates.crt

WORKDIR /toolkit

COPY docker/*.crt /usr/local/share/ca-certificates/
RUN update-ca-certificates

# dtrack core components
COPY ./pyproject.toml .
COPY ./src/dtracktoolkit/*.py src/dtracktoolkit/
COPY ./src/dtracktoolkit/api_token_manager/*.py src/dtracktoolkit/api_token_manager/
COPY ./src/dtracktoolkit/notification/*.py src/dtracktoolkit/notification/
COPY ./src/dtracktoolkit/project/*.py src/dtracktoolkit/project/

# dtracktoolkit-as-a-service components
COPY ./docker/src/*.py src/
COPY ./docker/src/mailer/*.py src/mailer/
COPY ./docker/service.py .
COPY ./docker/entrypoint.sh .

RUN pip install --upgrade pip && pip install . && pip install .[composer] && pip install .[sbom]

# best practice would be to mount these folders (output, log, config)
RUN mkdir output && mkdir log && mkdir config

# copy test files needed
COPY ./tests/*.py tests/
COPY ./docker/test-config.toml config/config.toml
COPY ./.coveragerc .

# tests needs write permission to home directory for temp files etc.
RUN if [ "$BUILD_ENV" = "TEST" ] ; then \
    pip install .[test]; \
    echo "pytest --cov-report xml:coverage/coverage.xml --cov=. tests/" > entrypoint.sh; \
    chmod -R 777 . ; \ 
else \
    rm config/*.toml; rm -R tests/; rm .coveragerc; \
fi

# Still debugging ...
RUN apk add tree && tree

RUN chmod +x entrypoint.sh
RUN adduser -S toolkit && chmod -R 777 log && chmod -R 777 output && chmod -R 777 config

USER toolkit

#CMD [ "python", "service.py" ]
CMD ["sh", "entrypoint.sh"]

