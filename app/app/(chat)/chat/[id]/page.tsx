import { Chat } from '@/components/chat';
import { notFound } from 'next/navigation';
import { getThreadState } from '../../actions';

export default async function Page(props: { params: Promise<{ id: string }> }) {
  const params = await props.params;
  const { id } = params;

  const threadState = await getThreadState(id);

  if (!threadState) {
    return notFound();
  }

  const { messages, context } = threadState;

  const domainId = context.domain_id!;


  return (
    <Chat
      key={id}
      id={id}
      initialMessages={messages}
      initialContext={context}
      selectedDomainId={domainId}
    />
  );
}
