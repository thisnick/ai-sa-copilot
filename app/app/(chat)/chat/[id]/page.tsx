import { cookies } from 'next/headers';
import { Chat } from '@/components/chat';
import { notFound } from 'next/navigation';
import { getThreadState, saveDomainId } from '../../actions';
import { createClient } from '@/lib/supabase/server';


export default async function Page(props: { params: Promise<{ id: string }> }) {
  const params = await props.params;
  const { id } = params;

  const threadState = await getThreadState(id);

  if (!threadState) {
    return notFound();
  }

  const { messages, context } = threadState;

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
      saveDomainId(domain.id);
    }
    else {
      domainIdFromCookie = "b54feb10-5011-429e-8585-35913d797d8e";
    }
  }

  return (
    <Chat
      key={id}
      id={id}
      initialMessages={messages}
      initialContext={context}
      selectedDomainId={domainIdFromCookie}
    />
  );
}
