"use client";

import OauthSignIn from '@/components/oauth-signin';
import { ProfileContext } from '@/components/profile-context';
import { redirect } from 'next/navigation';
import { useContext } from 'react';

import { BrainCircuitIcon } from '@/components/icons'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"


export default function SignIn() {
  // Check if the user is already logged in and redirect to the account page if so
  const { profile } = useContext(ProfileContext);

  if (profile) {
    return redirect('/');
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100 dark:bg-gray-900">
    <Card className="w-full max-w-md">
      <CardHeader className="space-y-1">
        <div className="flex items-center justify-center mb-4 text-blue-500">
          <BrainCircuitIcon size={48} />
        </div>
        <CardTitle className="text-2xl font-bold text-center">Run Book Maker</CardTitle>
        <CardDescription className="text-center">
          Create detailed step-by-step guides powered by AI research of product documentation.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <OauthSignIn />
        </div>
      </CardContent>
    </Card>
  </div>
  )
}
