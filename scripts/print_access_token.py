import asyncio
from api.lib.supabase import get_server_supabase_client

async def main():
  supabase = await get_server_supabase_client()
  user_response = await supabase.auth.sign_in_with_password({
    "email": "wiseyu@gmail.com",
    "password": "password"
  })
  assert user_response.user is not None, "Failed to sign in"
  session = await supabase.auth.get_session()
  assert session is not None, "Failed to get session"
  print(session.access_token)

if __name__ == "__main__":
  asyncio.run(main())
