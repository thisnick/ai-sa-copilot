"use server";

import OauthSignIn from '../components/oauth-signin';
import SignIn from './sign-in';


import { BrainCircuit } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

export default async function LoginPage() {
  return (
    <SignIn>
      <div className="min-h-screen flex items-center justify-center bg-gray-100 dark:bg-gray-900">
        <Card className="w-full max-w-md">
          <CardHeader className="space-y-1">
            <div className="flex items-center justify-center mb-4">
              <BrainCircuit className="h-12 w-12 text-blue-500" />
            </div>
            <CardTitle className="text-2xl font-bold text-center">Solutions Architect Copilot</CardTitle>
            <CardDescription className="text-center">
              Access your AI-powered solutions architect assistant. Sign up to get started.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <OauthSignIn />
            </div>
          </CardContent>
        </Card>
      </div>
    </SignIn>
  )
}

