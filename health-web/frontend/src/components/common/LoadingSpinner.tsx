export default function LoadingSpinner({ text = '로딩 중...' }: { text?: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 gap-3">
      <div className="w-8 h-8 border-3 border-primary-600 border-t-transparent rounded-full animate-spin" />
      <p className="text-sm text-gray-500">{text}</p>
    </div>
  );
}
