def test_register_login_and_create_project(client):
    register_response = client.post(
        "/api/auth/register",
        json={"login": "tester_01", "password": "secret123"},
    )
    assert register_response.status_code == 201

    login_response = client.post(
        "/api/auth/login",
        json={"login": "tester_01", "password": "secret123"},
    )
    assert login_response.status_code == 200
    csrf_token = client.cookies.get("csrf_token")
    assert csrf_token is not None

    create_response = client.post(
        "/api/projects",
        json={"title": "First project", "content": "hello"},
        headers={"X-CSRF-Token": csrf_token},
    )
    assert create_response.status_code == 200
    body = create_response.json()
    assert body["title"] == "First project"
    assert body["content"] == "hello"
    assert isinstance(body["id"], int)


def test_create_project_without_csrf_returns_403(client):
    client.post("/api/auth/register", json={"login": "tester_02", "password": "secret123"})
    client.post("/api/auth/login", json={"login": "tester_02", "password": "secret123"})

    response = client.post(
        "/api/projects",
        json={"title": "No csrf", "content": "x"},
    )
    assert response.status_code == 403

def test_register_duplicate_login_returns_400(client):
    client.post('/api/auth/register', json = {"login": "tester_03", "password": "password"})
    same_login_response = client.post('/api/auth/register', json = {"login": "tester_03", "password": "password"})
    assert same_login_response.status_code == 400

def test_wrong_password_returns_401(client):
    client.post('/api/auth/register', json={"login": "tester_03", "password": "password"})
    wrong_password_response = client.post('/api/auth/login', json = {"login": "tester_03", "password": "wrong_password"})
    assert wrong_password_response.status_code == 401

def test_logout_deletes_cookies(authorized_client):
    response = authorized_client.post('/api/auth/logout')
    assert response.status_code == 200
    assert "access_token" not in authorized_client.cookies and "csrf_token" not in authorized_client.cookies

def test_get_only_accessed_projects(create_authorized_client):
    owner_client = create_authorized_client('owner')
    stranger_client = create_authorized_client('stranger')

    pr_create_response = owner_client.post('api/projects/',
                                           json = {
        "title" : "title text",
        "content" : "content text",

    },headers = {"X-CSRF-Token" : owner_client.cookies.get("csrf_token")})

    stranger_get_response = stranger_client.get('api/projects/' + str(pr_create_response.json()["id"]))
    assert stranger_get_response.status_code == 404

    owner_client_get_response = owner_client.get('api/projects/' + str(pr_create_response.json()["id"]))
    assert owner_client_get_response.status_code == 200

def test_share_project(create_authorized_client):
    owner_client = create_authorized_client('owner')
    guest_client = create_authorized_client('guest')

    owner_create_response = owner_client.post('api/projects/',
                                           json={
                                               "title": "title text",
                                               "content": "content text",

                                           }, headers={"X-CSRF-Token": owner_client.cookies.get("csrf_token")})

    owner_share_response = owner_client.post(f'/api/projects/{owner_create_response.json()['id']}/share',
                                             json = {
                                                 "login" : "guest"
                                             },
                                             headers={"X-CSRF-Token": owner_client.cookies.get("csrf_token")}
                                             )
    assert owner_share_response.status_code == 200

    double_share_response = owner_client.post(f'/api/projects/{owner_create_response.json()['id']}/share',
                                             json={
                                                 "login": "guest"
                                             },
                                             headers={"X-CSRF-Token": owner_client.cookies.get("csrf_token")}
                                             )
    assert double_share_response.status_code == 400

    not_found_share_response = owner_client.post(f'/api/projects/{owner_create_response.json()['id']}/share',
                                             json={
                                                 "login": "not_found"
                                             },
                                             headers={"X-CSRF-Token": owner_client.cookies.get("csrf_token")}
                                             )

    assert not_found_share_response.status_code == 404

