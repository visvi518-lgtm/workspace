import { useState } from 'react';
import { Search } from 'lucide-react';

interface Props {
  onSearch: (query: string) => void;
  placeholder?: string;
  tags?: string[];
  onTagClick?: (tag: string) => void;
}

export default function SearchBar({ onSearch, placeholder = '검색어를 입력하세요', tags = [], onTagClick }: Props) {
  const [query, setQuery] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSearch(query.trim());
  };

  return (
    <div className="space-y-3">
      <form onSubmit={handleSubmit} className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={placeholder}
          className="input-base pl-10 pr-20"
        />
        <button
          type="submit"
          className="absolute right-2 top-1/2 -translate-y-1/2 btn-primary text-sm py-1.5 px-3"
        >
          검색
        </button>
      </form>

      {tags.length > 0 && (
        <div className="flex flex-wrap gap-2">
          <span className="text-sm text-gray-500">관련검색어:</span>
          {tags.map((tag) => (
            <button
              key={tag}
              onClick={() => onTagClick?.(tag)}
              className="tag"
            >
              #{tag}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
