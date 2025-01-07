'use client';

import { startTransition, useMemo, useOptimistic } from 'react';
import { saveDomainId } from '@/app/(chat)/actions';
import { cn } from '@/lib/utils';
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import useSWR from 'swr';
import { Tables } from '@/lib/supabase/database.types';
import { createClient } from '@/lib/supabase/client';

type ArtifactDomain = Tables<'artifact_domains'>;

export function DomainSelector({
  selectedDomainId,
  className,
}: {
  selectedDomainId: string;
  className?: string;
} & React.ComponentProps<typeof Select>) {
  const [optimisticDomainId, setOptimisticDomainId] = useOptimistic(selectedDomainId);

  const supabase = createClient();

  const {
    data: domains,
    isLoading: isDomainsFetching,
  } = useSWR<Array<ArtifactDomain>>(
    `/api/domain`,
    async () => {
      const { data, error } = await supabase
        .from('artifact_domains')
        .select('*')
        .eq('visibility', 'public')
        .order('name', { ascending: true });
      if (error) throw error;
      return data;
    },
  );

  const selectedDomain = useMemo(
    () => (domains || []).find((domain) => domain.id === optimisticDomainId),
    [domains, optimisticDomainId],
  );

  return (
    <div className={cn("flex items-center gap-4", className)}>
      <Label htmlFor="domain-select">Select domain for the run book:</Label>
      <Select
        value={optimisticDomainId}
        onValueChange={(value) => {
          startTransition(() => {
            setOptimisticDomainId(value);
            saveDomainId(value);
          });
        }}
      >
        <SelectTrigger id="domain-select" className="w-[300px]">
          <SelectValue placeholder="Select a domain" />
        </SelectTrigger>
        <SelectContent>
          {(domains || []).map((domain) => (
            <SelectItem key={domain.id} value={domain.id}>
              {domain.name}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      {isDomainsFetching && <p className="text-sm text-muted-foreground">Loading domains...</p>}
    </div>
  );
}

