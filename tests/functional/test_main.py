def test_index_route(client):
    response = client.get('/')
    assert response.status_code == 200
    # Check for some content we expect in the HTML
    assert b"ShellYeah!" in response.data
