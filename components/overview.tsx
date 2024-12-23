import { motion } from 'motion/react';
import Link from 'next/link';

import { MessageIcon } from './icons';

export const Overview = () => {
  return (
    <motion.div
      key="overview"
      className="max-w-3xl mx-auto md:mt-20"
      initial={{ opacity: 0, scale: 0.98 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.98 }}
      transition={{ delay: 0.5 }}
    >
      <div className="rounded-xl p-6 flex flex-col gap-8 leading-relaxed text-center max-w-xl">
        <p className="flex flex-row justify-center gap-4 items-center">
          <MessageIcon size={32} />
        </p>
        <p>
          This tool demonstrates creating comprehensive run books by analyzing a product's documentation.
          It researches and synthesizes the documentation and put them together as a single run book.
        </p>
        <p>
          For now, it only has documentation for Databricks, but more will be added.
        </p>
      </div>
    </motion.div>
  );
};
