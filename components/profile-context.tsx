"use client";
import { Tables } from "@/lib/supabase/database.types";
import { createClient } from "@/lib/supabase/client";
// import { usePostHog } from "posthog-js/react";
import { createContext, use, useEffect, useState } from "react";

export type Profile = {
  profile?: Tables<"profiles">,
  isLoading: boolean,
};

export const ProfileContext = createContext<Profile>({ isLoading: true });

export function ProfileContextProvider({ children }: { children: React.ReactNode }) {
  const [profile, setProfile] = useState<Profile>({ isLoading: true });

  // const posthog = usePostHog();

  useEffect(() => {
    const supabase = createClient();
    const fetchData = async () => {
      const { data: { session } } = await supabase.auth.getSession();
      const user = session?.user;
      if (!user) {
        setProfile({ isLoading: false });
        return;
      }
      const { data: profile } = await supabase
        .from('profiles')
        .select()
        .eq('user_id', user.id)
        .maybeSingle();

      if (!profile) {
        setProfile({ isLoading: false });
        return;
      }
      setProfile({ profile, isLoading: false });

    };

    fetchData();

    const { data: authListener } = supabase.auth.onAuthStateChange((_event, session) => {
    //   if (!session?.user && posthog) {
    //     posthog.capture('$signout');
    //     posthog.reset();
    // }
      fetchData();
    });

    return () => {
      authListener?.subscription.unsubscribe();
    };

  // }, [posthog]);
  }, []);

  return (
    <ProfileContext.Provider value={profile}>
      {children}
    </ProfileContext.Provider>
  );
}
