import asyncio
from dotenv import load_dotenv
from lib.supabase import create_async_supabase_admin_client

load_dotenv()


async def async_create_user(email: str, name: str):
  supabase = await create_async_supabase_admin_client()
  await supabase.auth.admin.create_user({
    "email": email,
    "user_metadata": {
      "name": name,
      "email": email,
    },
  })

def create_user(email: str, name: str):
  asyncio.run(async_create_user(email, name))


if __name__ == "__main__":
  import argparse

  parser = argparse.ArgumentParser(description='Create a new user')
  parser.add_argument('--email', required=True, help='User email address')
  parser.add_argument('--name', required=True, help='User name')

  args = parser.parse_args()
  create_user(args.email, args.name)
