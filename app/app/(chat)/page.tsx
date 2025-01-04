import { cookies } from 'next/headers';

import { Chat } from '@/components/chat';
import { generateUUID } from '@/lib/utils';
import { createClient } from '@/lib/supabase/server';

export default async function Page() {
  const id = generateUUID();

  const cookieStore = await cookies();
  let domainIdFromCookie = cookieStore.get('domain-id')?.value;
  if (!domainIdFromCookie) {
    const supabase = await createClient();
    const { data: domain, error } = await supabase.from('artifact_domains').select('id').limit(1).maybeSingle();
    if (error) {
      throw error;
    }
    if (domain) {
      domainIdFromCookie = domain.id;
    }
    else {
      domainIdFromCookie = "b54feb10-5011-429e-8585-35913d797d8e";
    }
  }

  return (
    <Chat
      key={id}
      id={id}
      initialMessages={[]}
      initialContext={{}}
      selectedDomainId={domainIdFromCookie}
    />
  );
}
