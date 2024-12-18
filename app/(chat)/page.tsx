import { cookies } from 'next/headers';

import { Chat } from '@/components/chat';
import { generateUUID } from '@/lib/utils';

export default async function Page() {
  const id = generateUUID();

  const cookieStore = await cookies();
  const modelIdFromCookie = cookieStore.get('model-id')?.value;

  const domainId = "b54feb10-5011-429e-8585-35913d797d8e"

  return (
    <Chat
      key={id}
      id={id}
      initialMessages={[]}
      domainId={domainId}
    />
  );
}
