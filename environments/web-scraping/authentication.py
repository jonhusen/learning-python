import msal

def o365_auth(clientid, authority, scope):
    """
    Takes the client id of an app registration and the authentication
    url as authority to initiate the device-flow authentication.
    User will need to enter the device code into the authorization site
    to complete authentication.

    :param clientid: AppID/ClientID of the Azure App Registration
    :param authority: Login page used to authenticate
    :param scope: Permissions requested
    :return: Authentication token
    """
    global headers

    app = msal.PublicClientApplication(client_id=clientid, authority=authority)
    token = None
    headers = None
    accounts = app.get_accounts()

    if accounts:
        for a in accounts:
            print(a["username"])
            if input("Select this account? y/n") == "y":
                chosen = a
                break
        token = app.acquire_token_silent(scope, account=chosen)

    if not token:
        flow = app.initiate_device_flow(scopes=scope)
        if "user_code" not in flow:
            raise ValueError(
                "Fail to create device flow. Err: %s" % json.dumps(flow, indent=4)
            )
        print(flow["message"])
        sys.stdout.flush()
        token = app.acquire_token_by_device_flow(flow)

    if "access_token" in token:
        headers = {"Authorization": "Bearer " + token["access_token"]}
        graph_data = requests.get(url=endpoint, headers=headers).json()
        print("Graph API call result = %s" % json.dumps(graph_data, indent=2))
    else:
        print(token.get("error"))
        print(token.get("error_description"))
        print(token.get("correlation_id"))
    return token
