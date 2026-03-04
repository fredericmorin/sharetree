# sharetree

File sharing with

## Dev

Techstack: Python/sqla/fastapi/sqlite/vue

* Create venv and install deps
    ```sh
    bin/setup-dev.sh
    ```


# Featureset

- [ ] Share existing folder tree
    - [ ] No upload function
- [ ] Admin side
    - [ ] Auth based on either of
        - [ ] trusted headers admins group enabled through env
        - [ ] magic user/pass from env
        - [ ] IP subnet range
    - [ ] Custom forward auth api
    - [ ] File and folder access granting api
- [ ] User side
    - [ ] Trade access code for session access
    - [ ] View accessible files api


# Deploy

- [ ] Deploy as docker
    - [ ] Python app
    - [ ] Option to also run Caddy serve with forward auth
- [ ] Redis?


# Refs

- https://medium.com/@aahana.khanal11/scaling-a-fastapi-application-handling-multiple-requests-at-once-e5c128720c95
