'use client'

import * as React from "react"
import Link from "next/link"
import { ExternalLink, ChevronRight } from 'lucide-react'
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { RunbookSection, ArtifactWithLinks, ContextVariables } from "@/lib/api/types"
import { Markdown } from "./markdown"

interface RunbookOutlineProps {
  runbook_sections: RunbookSection[];
  saved_artifacts: Record<string, ArtifactWithLinks[]>;
}

function RelatedArtifacts({ artifactIds, savedArtifacts }: { artifactIds: string[], savedArtifacts: Record<string, ArtifactWithLinks[]> }) {
  const artifacts = artifactIds.flatMap(id =>
    Object.values(savedArtifacts).flat().filter(artifact => artifact.artifact_id === id)
  );

  if (artifacts.length === 0) return null;

  return (
    <div className="mt-4">
      <h4 className="text-sm font-medium mb-2">Related Resources:</h4>
      <ul className="space-y-2">
        {artifacts.map((artifact) => (
          <li key={artifact.artifact_id}>
            <Link
              href={artifact.url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-primary"
            >
              <ChevronRight className="h-3 w-3" />
              {artifact.title}
              <ExternalLink className="h-3 w-3 ml-1" />
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}

export function RunbookOutline({ runbook_sections, saved_artifacts }: RunbookOutlineProps) {
  return (
    <ScrollArea className="h-[calc(100vh-4rem)]">
      <div className="p-4">
        <Card>
          <CardHeader>
            <CardTitle>Runbook Outline</CardTitle>
          </CardHeader>
          <CardContent>
            <Accordion type="multiple" className="w-full">
              {runbook_sections.map((section, index) => (
                <AccordionItem key={index} value={`section-${index}`}>
                  <AccordionTrigger className="hover:no-underline">
                    <div className="flex items-center justify-between w-full">
                      <span>{section.section_title}</span>
                      <Badge variant="secondary" className="ml-2">
                        {section.related_artifacts.length}
                      </Badge>
                    </div>
                  </AccordionTrigger>
                  <AccordionContent>
                    <div className="text-sm text-muted-foreground mb-4">
                      <Markdown className="prose-sm max-w-none">{section.outline}</Markdown>
                    </div>
                    <RelatedArtifacts
                      artifactIds={section.related_artifacts}
                      savedArtifacts={saved_artifacts}
                    />
                  </AccordionContent>
                </AccordionItem>
              ))}
            </Accordion>
          </CardContent>
        </Card>
      </div>
    </ScrollArea>
  );
}

