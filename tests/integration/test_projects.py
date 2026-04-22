def test_new_user_gets_empty_project_list(authorized_client):
    response = authorized_client.get('api/projects')

    assert response.json() == []

def test_update_project(authorized_client):
    post_response = authorized_client.post('/api/projects', json={
        "title": "test project title",
        "content": "test project content"
    }, headers={"X-CSRF-Token": authorized_client.cookies.get("csrf_token")})
    authorized_client.put(f"/api/projects/{post_response.json()['id']}", json = {
        "title": "edited title",
        "content": "edited content"
    }, headers={"X-CSRF-Token": authorized_client.cookies.get("csrf_token")})

    get_reponse = authorized_client.get(f"/api/projects/{post_response.json()['id']}")
    assert get_reponse.json()['title'] == "edited title" and get_reponse.json()['content'] == "edited content"

