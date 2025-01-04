'use client';

import { Button } from '@/components/ui/button';
import { type Provider } from '@supabase/supabase-js';
import { GithubIcon } from '@/components/icons';
import { JSX, useState } from 'react';
import { createClient } from '@/lib/supabase/client';
import { getURL } from '@/lib/navigation';
import { Loader2 } from 'lucide-react'
type OAuthProviders = {
  name: Provider;
  displayName: string;
  icon: JSX.Element;
};

export default function OauthSignIn() {
  const oAuthProviders: OAuthProviders[] = [
    {
      name: 'github',
      displayName: 'GitHub',
      icon: <GithubIcon size={16} />
    }
    /* Add desired OAuth providers here */
  ];
  const [loadingProvider, setLoadingProvider] = useState<Provider | null>(null);

  const onLogin = async (provider: Provider) => {
    setLoadingProvider(provider);
    const supabase = await createClient();
    await supabase.auth.signInWithOAuth({
      provider: provider,
      options: {
        redirectTo: getURL('/auth/callback'),
        queryParams: {
          next: '/chat'
        }
      }
    });
    // Note: We don't need to reset loading state since we're redirecting
  };

  return (
    <div className="mt-8">
      {oAuthProviders.map((provider) => (
        <form
          key={provider.name}
          className="pb-2"
        >
          <input type="hidden" name="provider" value={provider.name} />
          <Button
            variant="default"
            type="submit"
            className="w-full"
            size="sm"
            disabled={loadingProvider !== null}
            onClick={e => {
              e.preventDefault();
              onLogin(provider.name);
            }}
          >

              {loadingProvider === provider.name ? (
                // You can replace this with your preferred loading spinner component
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <span className="mr-2">
                  {provider.icon}
                </span>
              )}

            <span>
              {loadingProvider === provider.name
                ? 'Signing in...'
                : `Sign in with ${provider.displayName}`}
            </span>
          </Button>
        </form>
      ))}
    </div>
  );
}
