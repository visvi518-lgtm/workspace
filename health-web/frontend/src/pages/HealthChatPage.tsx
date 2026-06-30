import { useState, useRef, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Send, Plus, MessageSquare, Bot, User, BookOpen, Trash2, Menu, X } from 'lucide-react';
import { chatApi } from '@/services/api';
import type { ChatSession, ChatMessage } from '@/types';
import { format } from 'date-fns';
import toast from 'react-hot-toast';

export default function HealthChatPage() {
  const qc = useQueryClient();
  const [selectedSession, setSelectedSession] = useState<number | null>(null);
  const [input, setInput] = useState('');
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  const { data: sessions = [] } = useQuery<ChatSession[]>({
    queryKey: ['chatSessions'],
    queryFn: () => chatApi.getSessions().then((r) => r.data),
  });

  const { data: messages = [], isLoading: msgLoading } = useQuery<ChatMessage[]>({
    queryKey: ['chatMessages', selectedSession],
    queryFn: () => chatApi.getMessages(selectedSession!).then((r) => r.data),
    enabled: !!selectedSession,
  });

  const createSession = useMutation({
    mutationFn: () => chatApi.createSession(),
    onSuccess: (res) => {
      qc.invalidateQueries({ queryKey: ['chatSessions'] });
      setSelectedSession(res.data.id);
    },
  });

  const sendMessage = useMutation({
    mutationFn: () => chatApi.sendMessage(selectedSession!, input),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['chatMessages', selectedSession] });
      setInput('');
    },
    onError: () => toast.error('메시지 전송에 실패했습니다.'),
  });

  const deleteSession = useMutation({
    mutationFn: (id: number) => chatApi.deleteSession(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['chatSessions'] });
      setSelectedSession(null);
    },
  });

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || !selectedSession) return;
    sendMessage.mutate();
  };

  const sessionList = (
    <>
      {sessions.length === 0 && (
        <p className="text-xs text-gray-400 text-center py-4">상담 내역이 없습니다.</p>
      )}
      {sessions.map((s) => (
        <div
          key={s.id}
          className={`group flex items-center justify-between px-3 py-2 rounded-lg cursor-pointer transition-colors text-sm
            ${selectedSession === s.id ? 'bg-primary-100 text-primary-700' : 'hover:bg-gray-100 text-gray-700'}`}
          onClick={() => { setSelectedSession(s.id); setMobileSidebarOpen(false); }}
        >
          <div className="flex items-center gap-2 min-w-0">
            <MessageSquare className="w-3.5 h-3.5 flex-shrink-0" />
            <span className="truncate">{s.title}</span>
          </div>
          <button
            onClick={(e) => { e.stopPropagation(); deleteSession.mutate(s.id); }}
            className="opacity-0 group-hover:opacity-100 text-gray-400 hover:text-red-500 transition-opacity"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        </div>
      ))}
    </>
  );

  return (
    <div className="flex h-[calc(100vh-9rem)] gap-4">
      {/* Desktop Sidebar */}
      <div className="hidden sm:flex w-64 flex-shrink-0 flex-col gap-2">
        <button
          onClick={() => createSession.mutate()}
          className="btn-primary flex items-center gap-2 w-full justify-center"
        >
          <Plus className="w-4 h-4" /> 새 상담
        </button>

        <div className="card flex-1 overflow-y-auto p-2 space-y-1">
          <p className="text-xs font-medium text-gray-400 px-2 py-1">상담 내역</p>
          {sessionList}
        </div>
      </div>

      {/* Mobile Sidebar Overlay */}
      {mobileSidebarOpen && (
        <div className="fixed inset-0 z-40 sm:hidden">
          <div className="absolute inset-0 bg-black/40" onClick={() => setMobileSidebarOpen(false)} />
          <div className="absolute top-0 left-0 bottom-0 w-72 bg-white shadow-xl flex flex-col p-4 gap-3">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-gray-900 text-sm">상담 내역</span>
              <button
                onClick={() => setMobileSidebarOpen(false)}
                className="p-1 text-gray-400 hover:text-gray-600 rounded"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <button
              onClick={() => { createSession.mutate(); setMobileSidebarOpen(false); }}
              className="btn-primary flex items-center gap-2 w-full justify-center"
            >
              <Plus className="w-4 h-4" /> 새 상담
            </button>
            <div className="flex-1 overflow-y-auto space-y-1">
              {sessionList}
            </div>
          </div>
        </div>
      )}

      {/* Chat area - full width on mobile */}
      <div className="flex-1 flex flex-col card p-0 overflow-hidden min-w-0">
        {/* Mobile top bar */}
        <div className="sm:hidden flex items-center gap-2 px-4 py-2.5 border-b border-gray-100">
          <button
            onClick={() => setMobileSidebarOpen(true)}
            className="flex items-center gap-1.5 text-sm text-gray-600 hover:text-primary-600 transition-colors"
          >
            <Menu className="w-4 h-4" /> 상담 내역
          </button>
          {selectedSession && (
            <span className="ml-auto text-xs text-gray-400 truncate max-w-[180px]">
              {sessions.find((s) => s.id === selectedSession)?.title}
            </span>
          )}
        </div>

        {!selectedSession ? (
          <div className="flex-1 flex flex-col items-center justify-center text-center p-8 text-gray-400 gap-4">
            <Bot className="w-16 h-16 text-primary-200" />
            <div>
              <p className="font-medium text-gray-600">건강 상담 AI</p>
              <p className="text-sm mt-1">의료 논문 기반으로 안전하고 근거 있는 답변을 드립니다.</p>
              <p className="text-xs mt-3 text-gray-400">
                ⚠ 본 서비스는 의료 진단을 대체하지 않습니다.
              </p>
            </div>
            <button onClick={() => createSession.mutate()} className="btn-primary">
              상담 시작하기
            </button>
          </div>
        ) : (
          <>
            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {msgLoading && (
                <div className="text-center text-sm text-gray-400 py-8">불러오는 중...</div>
              )}
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}
                >
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0
                    ${msg.role === 'user' ? 'bg-primary-600' : 'bg-gray-200'}`}>
                    {msg.role === 'user'
                      ? <User className="w-4 h-4 text-white" />
                      : <Bot className="w-4 h-4 text-gray-600" />}
                  </div>
                  <div className={`max-w-[75%] ${msg.role === 'user' ? 'items-end' : 'items-start'} flex flex-col gap-1`}>
                    <div
                      className={`rounded-2xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap
                        ${msg.role === 'user'
                          ? 'bg-primary-600 text-white rounded-tr-sm'
                          : 'bg-gray-100 text-gray-800 rounded-tl-sm'}`}
                    >
                      {msg.content}
                    </div>
                    {msg.references && msg.references.length > 0 && (
                      <div className="bg-blue-50 border border-blue-100 rounded-lg p-2 text-xs text-blue-700 space-y-1">
                        <p className="font-medium flex items-center gap-1">
                          <BookOpen className="w-3 h-3" /> 참고 논문
                        </p>
                        {msg.references.map((ref, i) => (
                          <div key={i}>
                            {ref.url ? (
                              <a href={ref.url} target="_blank" rel="noopener noreferrer" className="hover:underline">
                                {ref.title} {ref.year && `(${ref.year})`}
                              </a>
                            ) : (
                              <span>{ref.title} {ref.year && `(${ref.year})`}</span>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                    <span className="text-xs text-gray-400">
                      {format(new Date(msg.created_at), 'HH:mm')}
                    </span>
                  </div>
                </div>
              ))}
              {sendMessage.isPending && (
                <div className="flex gap-3">
                  <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center">
                    <Bot className="w-4 h-4 text-gray-600" />
                  </div>
                  <div className="bg-gray-100 rounded-2xl rounded-tl-sm px-4 py-3">
                    <div className="flex gap-1">
                      {[0, 1, 2].map((i) => (
                        <div key={i} className="w-2 h-2 rounded-full bg-gray-400 animate-bounce"
                          style={{ animationDelay: `${i * 0.15}s` }} />
                      ))}
                    </div>
                  </div>
                </div>
              )}
              <div ref={bottomRef} />
            </div>

            {/* Input */}
            <div className="border-t border-gray-100 p-4">
              <p className="text-xs text-gray-400 mb-2">
                ⚠ 건강 상담은 참고용이며 의료 진단을 대체하지 않습니다.
              </p>
              <form onSubmit={handleSend} className="flex gap-2">
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="증상이나 건강 관련 질문을 입력하세요"
                  className="input-base flex-1"
                />
                <button
                  type="submit"
                  disabled={!input.trim() || sendMessage.isPending}
                  className="btn-primary px-4"
                >
                  <Send className="w-4 h-4" />
                </button>
              </form>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
