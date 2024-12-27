'use client';

import { Button } from '@/components/ui/button';
import { type Provider } from '@supabase/supabase-js';
import { GithubIcon } from '@/components/icons';
import { JSX, useState } from 'react';
import { createClient } from '@/lib/supabase/client';
import { getURL } from '@/lib/navigation';
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
  const [isSubmitting, setIsSubmitting] = useState(false);

  const onLogin = async (provider: Provider) => {
    setIsSubmitting(true); // Disable the button while the request is being handled
    const supabase = await createClient();
    const { data, error } = await supabase.auth.signInWithOAuth({
      provider: provider,
      options: {
        redirectTo: getURL('/auth/callback'),
        queryParams: {
          next: '/chat'
        }
      }
    });

    setIsSubmitting(false);
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
            disabled={isSubmitting}
            onClick={e => {
              e.preventDefault();
              onLogin(provider.name);
            }}
          >
            <span className="mr-2">{provider.icon}</span>
            <span>Sign in with {provider.displayName}</span>
          </Button>
        </form>
      ))}
    </div>
  );
}
