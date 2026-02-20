import React, { useEffect } from 'react';

interface SeoHeadProps {
  title: string;
  description: string;
  canonicalPath?: string;
  locale?: 'ru_RU' | 'en_US';
}

const ensureMeta = (selector: string, create: () => HTMLMetaElement): HTMLMetaElement => {
  const existing = document.querySelector(selector) as HTMLMetaElement | null;
  if (existing) {
    return existing;
  }
  const created = create();
  document.head.appendChild(created);
  return created;
};

const ensureCanonical = (): HTMLLinkElement => {
  const existing = document.querySelector('link[rel="canonical"]') as HTMLLinkElement | null;
  if (existing) {
    return existing;
  }
  const link = document.createElement('link');
  link.setAttribute('rel', 'canonical');
  document.head.appendChild(link);
  return link;
};

export const SeoHead: React.FC<SeoHeadProps> = React.memo(
  ({ title, description, canonicalPath = '/', locale = 'ru_RU' }) => {
    useEffect(() => {
      const canonicalUrl = `https://pandapal.ru${canonicalPath}`;
      document.title = title;

    const descriptionMeta = ensureMeta('meta[name="description"]', () => {
      const m = document.createElement('meta');
      m.setAttribute('name', 'description');
      return m;
    });
    descriptionMeta.setAttribute('content', description);

    const ogTitleMeta = ensureMeta('meta[property="og:title"]', () => {
      const m = document.createElement('meta');
      m.setAttribute('property', 'og:title');
      return m;
    });
    ogTitleMeta.setAttribute('content', title);

    const ogDescriptionMeta = ensureMeta('meta[property="og:description"]', () => {
      const m = document.createElement('meta');
      m.setAttribute('property', 'og:description');
      return m;
    });
    ogDescriptionMeta.setAttribute('content', description);

    const ogUrlMeta = ensureMeta('meta[property="og:url"]', () => {
      const m = document.createElement('meta');
      m.setAttribute('property', 'og:url');
      return m;
    });
    ogUrlMeta.setAttribute('content', canonicalUrl);

    const ogLocaleMeta = ensureMeta('meta[property="og:locale"]', () => {
      const m = document.createElement('meta');
      m.setAttribute('property', 'og:locale');
      return m;
    });
    ogLocaleMeta.setAttribute('content', locale);

    const twitterTitleMeta = ensureMeta('meta[name="twitter:title"]', () => {
      const m = document.createElement('meta');
      m.setAttribute('name', 'twitter:title');
      return m;
    });
    twitterTitleMeta.setAttribute('content', title);

    const twitterDescriptionMeta = ensureMeta('meta[name="twitter:description"]', () => {
      const m = document.createElement('meta');
      m.setAttribute('name', 'twitter:description');
      return m;
    });
    twitterDescriptionMeta.setAttribute('content', description);

      const canonical = ensureCanonical();
      canonical.setAttribute('href', canonicalUrl);
    }, [title, description, canonicalPath, locale]);

    return null;
  }
);

SeoHead.displayName = 'SeoHead';
