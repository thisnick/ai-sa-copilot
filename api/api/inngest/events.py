import inngest
from pydantic import BaseModel, Field
from typing import ClassVar, Generic, List, TypeVar, Type
from typing_extensions import Self  # For Python < 3.11

TEvent = TypeVar("TEvent", bound="BaseEvent")

class BaseEvent(BaseModel):
  data: BaseModel
  id: str = ""
  name: ClassVar[str]
  ts: int = 0

  @classmethod
  def from_event(cls: type[TEvent], event: inngest.Event) -> TEvent:
    return cls.model_validate(event.model_dump(mode="json"))

  def to_event(self) -> inngest.Event:
    return inngest.Event(
      name=self.name,
      data=self.data.model_dump(mode="json"),
      id=self.id,
      ts=self.ts,
    )

class CrawlRequestedEventData(BaseModel):
  url: str = Field(description="The URL to crawl")
  crawl_depth: int = Field(description="The depth of the crawl")
  domain_id: str = Field(description="The ID of the domain to crawl")

class CrawlRequestedEvent(BaseEvent):
  data: CrawlRequestedEventData
  name: ClassVar[str] = "app/url.added"

class ResumeCrawlEventData(BaseModel):
  domain_id: str = Field(description="The ID of the domain to crawl")

class ResumeCrawlEvent(BaseEvent):
  data: ResumeCrawlEventData
  name: ClassVar[str] = "app/crawl.resume"
