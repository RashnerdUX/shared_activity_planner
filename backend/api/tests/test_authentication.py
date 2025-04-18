from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes

from ..models import CustomUser


class AuthenticationTests(APITestCase):

    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username="Thor",
            email="Thor@asgard.com",
            password="mjolnirIsKing!!",
            first_name="Thor",
            last_name="Odinson"
        )

        self.token = default_token_generator.make_token(self.user)
        refresh = RefreshToken.for_user(self.user)
        self.refreshtoken = str(refresh)
        self.accesstoken = str(refresh.access_token)

    def test_register_user(self):
        url = reverse('register_new_user')
        data = {
                "username":"Loki",
                "email":"thegodofStories@asgard.com",
                "password":"mischiefin_my_blood",
                "first_name":"Loki",
                "last_name":"Laufeyson"
            }
        response = self.client.post(path=url, data=data)

        #This confirms that the request worked
        self.assertEqual(response.status_code, 201)
        #This checks if the object is now in the database
        self.assertEqual(CustomUser.objects.count(), 2)
        #This checks if the object was properly created
        self.assertEqual(CustomUser.objects.get(email="thegodofStories@asgard.com").username, "Loki")
    
    def test_login_user(self):
        """
        Normal behaviour allows the endpoint to authenticate with email first even if all 3 are passed
        """

        url = reverse('login_user')
        data = {
            "username":"Thor",
            "email":"Thor@asgard.com",
            "password":"mjolnirIsKing!!"
        }
        response = self.client.post(url, data)

        try:
            response_data = response.json()
        except ValueError:
            self.fail("Valid JSON was returned from the Login view")

        #This checks the status of the request
        self.assertEqual(response.status_code, 200, "Request was successful")
        #This checks that the refresh and access tokens were sent
        self.assertIn(member="refresh_token", container=response_data, msg="Refresh token was not returned")
        self.assertIn("access_token", response_data, "Access token was not returned")
        #This checks if the tokens are legit by decoding them and sending a fail method
        try:
            RefreshToken(response_data['refresh_token'])
            AccessToken(response_data['access_token'])
        except Exception as e:
            self.fail(f"Tokens are not valid: {str(e)}")

    def test_password_reset(self):
        reset_request_url = reverse("reset_password_request")
        reset_confirm_url = reverse("reset_password_confirm")

        #The reset request view expects an email
        data = {
            "email":"Thor@asgard.com"
        }

        #The reset confirm view expects the following
        reset_data = {  
            "uid":urlsafe_base64_encode(force_bytes(self.user.id)),
            "token":self.token,
            "new_password":"IamThe3eyedRav3n",
            "new_password_confirm":"IamThe3eyedRav3n"
        }

        reset_request_response = self.client.post(reset_request_url, data)
        reset_confirm_response = self.client.post(reset_confirm_url, reset_data)

        #This checks that the password reset requests were successful
        self.assertEqual(reset_request_response.status_code, 200)
        self.assertEqual(reset_confirm_response.status_code, 200)

        #After resetting password, this checks to ensure it has changed
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("IamThe3eyedRav3n"))
        self.assertFalse(self.user.check_password("mjolnirIsKing!!"))

    def test_logout_user(self):
        url = reverse("logout_user")
        access_refresh_url = reverse("token_refresh")
        data = {
            "refresh_token":self.refreshtoken,
            "access_token":self.accesstoken,
        }

        response = self.client.post(path=url, data=data, content_type="application/json", headers={"Authorization":f"Bearer {self.accesstoken}"})

        #This checks that the request was succesful
        self.assertEqual(response.status_code, 200)
        #This checks if the token was blacklisted
        new_response = self.client.post(path=access_refresh_url, data={"refresh":self.refreshtoken})
        self.assertEqual(new_response.status_code, 401)
