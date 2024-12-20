'use client'

import * as React from "react"
import Link from "next/link"
import { ExternalLink } from 'lucide-react'
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Separator } from "@/components/ui/separator"

import { ArtifactWithLinks } from "@/lib/api/types"

interface DocumentationViewerProps {
  savedArtifacts: Record<string, ArtifactWithLinks[]>
}

function ArticleLinks({ title, links }: { title: string; links: Array<{ title: string; url: string }> }) {
  if (!links?.length) return null

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <h4 className="text-sm font-medium">{title}</h4>
        <Badge variant="secondary" className="h-5">
          {links.length}
        </Badge>
      </div>
      <ul className="grid gap-1.5">
        {links.map((link, index) => (
          <li key={index}>
            <Link
              href={link.url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-primary"
            >
              {link.title}
              <ExternalLink className="h-3 w-3" />
            </Link>
          </li>
        ))}
      </ul>
    </div>
  )
}

function Article({ artifact }: { artifact: ArtifactWithLinks }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-start justify-between gap-4 text-lg">
          <Link
            href={artifact.url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-muted-foreground hover:text-primary text-base"
          >
            {artifact.title}
          </Link>
        </CardTitle>
        <CardDescription>{artifact.summary}</CardDescription>
      </CardHeader>
      {/* {(artifact.inbound_links?.length || artifact.outbound_links?.length) && (
        <CardContent className="grid gap-4">
          {artifact.inbound_links && (
            <>
              <ArticleLinks title="Referenced by" links={artifact.inbound_links} />
              {artifact.outbound_links && <Separator />}
            </>
          )}
          {artifact.outbound_links && (
            <ArticleLinks title="References" links={artifact.outbound_links} />
          )}
        </CardContent>
      )} */}
    </Card>
  )
}

export function DocumentationViewer({ savedArtifacts }: DocumentationViewerProps) {
  return (
    <ScrollArea className="h-[calc(100vh-9rem)]">
      <div className="p-4">
        <Accordion type="multiple" className="grid gap-4" defaultValue={[Object.keys(savedArtifacts)[0]]}>
          {Object.entries(savedArtifacts).map(([topic, artifacts], index) => (
            <AccordionItem key={index} value={topic} className="border-none">
              <AccordionTrigger className="rounded-lg border px-4 py-2 hover:bg-muted/50 hover:no-underline [&[data-state=open]]:rounded-b-none">
                {topic}
              </AccordionTrigger>
              <AccordionContent className="grid gap-4 rounded-b-lg border border-t-0 p-4 pt-4">
                {artifacts.map((artifact) => (
                  <Article key={artifact.artifact_id} artifact={artifact} />
                ))}
              </AccordionContent>
            </AccordionItem>
          ))}
        </Accordion>
      </div>
    </ScrollArea>
  )
}

