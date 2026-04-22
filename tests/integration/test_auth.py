def test_register_with_short_login_returns_422(client):
    register_response = client.post('/api/auth/register',
                                    json = {"login": "sht", "password": "password"})

    assert register_response.status_code == 422

def test_register_no_password(client):
    register_response = client.post('/api/auth/register',
                                    json = {"login": "login"})

    assert register_response.status_code == 422

def test_login_non_existent_login(client):
    login_response = client.post('/api/auth/login',
                                 json = {"login": "non_existent_login", "password": "password"})
    assert login_response.status_code == 401

