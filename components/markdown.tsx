import React, { ReactNode, memo } from 'react';
import ReactMarkdown, { Components } from 'react-markdown';
import remarkGfm from 'remark-gfm';
import Link from "next/link";

const generateSlug = (str: string) => {
  str = str?.replace(/^\s+|\s+$/g, '');
  str = str?.toLowerCase();
  const from = 'àáãäâèéëêìíïîòóöôùúüûñç·/_,:;';
  const to = 'aaaaaeeeeiiiioooouuuunc------';

  for (let i = 0, l = from.length; i < l; i++) {
    str = str.replace(new RegExp(from.charAt(i), 'g'), to.charAt(i));
  }

  str = str
    ?.replace(/[^a-z0-9 -]/g, '')
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-');

  return str;
};

const getSlugFromNode = (node: ReactNode): string => {
  if (typeof node === 'string') {
    return generateSlug(node);
  } else if (Array.isArray(node)) {
    return node.map(getSlugFromNode).join('-');
  } else if (React.isValidElement(node) && "props" in node && "children" in (node.props as any)) {
    return getSlugFromNode((node.props as any).children);
  } else {
    return '';
  }
};

export const components: Partial<Components> = {
  a: ({ ...props }) => (
    <Link
      target={props.target || props.href?.startsWith("#") ? "_self" : "_blank"}
      rel="noopener noreferrer"
      href={props.href || "#"}
      {...props}
    />
  ),
  h1: ({ children, ...props }) => (
    <h1 id={getSlugFromNode(children)} {...props}>
      {children}
    </h1>
  ),
  h2: ({ children, ...props }) => (
    <h2 id={getSlugFromNode(children)} {...props}>
      {children}
    </h2>
  ),
  h3: ({ children, ...props }) => (
    <h3 id={getSlugFromNode(children)} {...props}>
      {children}
    </h3>
  ),
};

interface MarkdownProps {
  children: ReactNode;
  className?: string;
}

const NonMemoizedMarkdown: React.FC<MarkdownProps> = ({ children, className }) => {
  const content = typeof children === 'string' ? (
    <ReactMarkdown
      className={`prose dark:prose-invert prose-a:link prose-a:link-secondary prose-a:link-hover ${className}`}
      remarkPlugins={[remarkGfm]}
      components={components}
    >
      {children}
    </ReactMarkdown>
  ) : (
    children
  );

  return <>{content}</>;
};

export const Markdown = memo(
  NonMemoizedMarkdown,
  (prevProps, nextProps) => prevProps.children === nextProps.children,
);
