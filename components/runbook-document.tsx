'use client'

import * as React from "react"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import { RunbookSection } from "@/lib/api/types"
import { Markdown } from "./markdown"

interface RunbookDocumentProps {
  runbook_sections: RunbookSection[];
}

export function RunbookDocument({ runbook_sections }: RunbookDocumentProps) {
  const [activeSection, setActiveSection] = React.useState<string | null>(null);

  const sectionRefs = React.useRef<{ [key: string]: HTMLElement | null }>({});

  React.useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setActiveSection(entry.target.id);
          }
        });
      },
      { rootMargin: "-50px 0px -50% 0px" }
    );

    Object.values(sectionRefs.current).forEach((ref) => {
      if (ref) observer.observe(ref);
    });

    return () => observer.disconnect();
  }, []);

  return (
    <div className="flex h-[calc(100vh-9rem)]">
      <Card className="w-64 h-full overflow-hidden hidden lg:block shrink-0">
        <CardHeader>
          <CardTitle>Table of Contents</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <ScrollArea className="h-[calc(100vh-14rem)]">
            <nav className="space-y-1 p-4">
              {runbook_sections.map((section, index) => (
                <a
                  key={index}
                  href={`#section-${index}`}
                  className={`block py-2 px-3 text-sm rounded-md transition-colors ${
                    activeSection === `section-${index}`
                      ? "bg-primary text-primary-foreground"
                      : "hover:bg-muted"
                  }`}
                  onClick={(e) => {
                    e.preventDefault();
                    sectionRefs.current[`section-${index}`]?.scrollIntoView({
                      behavior: "smooth",
                    });
                  }}
                >
                  {section.section_title}
                </a>
              ))}
            </nav>
          </ScrollArea>
        </CardContent>
      </Card>
      <Card className="flex-grow ml-4 h-full overflow-hidden">
        <CardHeader>
          <CardTitle>Runbook Document</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <ScrollArea className="h-[calc(100vh-14rem)]">
            <div className="p-6 space-y-8">
              {runbook_sections.map((section, index) => (
                <section
                  key={index}
                  id={`section-${index}`}
                  ref={(el) => { sectionRefs.current[`section-${index}`] = el }}
                  className="space-y-4"
                >
                  <Markdown className="max-w-none prose-sm w-[calc(100vw-5rem)] md:w-[calc(100vw-30rem)] lg:w-[calc(100vw-47rem)]">{section.content || ''}</Markdown>
                </section>
              ))}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  );
}

