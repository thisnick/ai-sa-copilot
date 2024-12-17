"use client";

import { Card } from '@/components/ui/card';
import OauthSignIn from '../components/oauth-signin';
import { ProfileContext } from '@/components/profile-context';
import { redirect } from 'next/navigation';
import { useContext } from 'react';

export default function SignIn({ children }: { children: React.ReactNode }) {
  // Check if the user is already logged in and redirect to the account page if so
  const { profile } = useContext(ProfileContext);

  if (profile) {
    return redirect('/');
  }

  return children;
}
