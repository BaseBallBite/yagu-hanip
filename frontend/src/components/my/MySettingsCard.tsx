import { Settings, ChevronRight, HelpCircle, Lightbulb } from 'lucide-react';

interface MySettingsCardProps {
  onNavigate: (path: string) => void;
}

export function MySettingsCard({ onNavigate }: MySettingsCardProps) {
  return (
    <div className="space-y-4">
      <div className="bg-white rounded-3xl p-6 border border-gray-100 shadow-sm transition-all duration-300 hover:shadow-md">
        <div className="flex items-center gap-2 mb-5">
          <span className="w-8 h-8 rounded-xl bg-purple-50 flex items-center justify-center shadow-xs">
            <Settings className="w-4 h-4 text-purple-600" />
          </span>
          <h2 className="text-lg font-bold text-gray-900 tracking-tight">설정</h2>
        </div>
        <div className="flex items-center justify-between gap-3 py-2">
          <div>
            <p className="text-sm font-semibold text-gray-900">응원 팀 변경</p>
            <p className="text-xs text-gray-500 mt-0.5">KBO 10개 구단 중 언제든 변경할 수 있어요.</p>
          </div>
          <button
            type="button"
            onClick={() => onNavigate('/team-select')}
            className="shrink-0 px-3 py-1.5 rounded-xl border border-gray-200 hover:border-purple-300 hover:bg-purple-50 text-xs font-semibold text-gray-700 hover:text-purple-700 flex items-center gap-1 transition cursor-pointer"
          >
            변경하기 <ChevronRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
      <button
        type="button"
        onClick={() => onNavigate('/guide')}
        className="w-full bg-white rounded-2xl p-4 border border-gray-100 shadow-sm hover:shadow-md hover:border-purple-200 transition-all flex items-center justify-between gap-3 text-left cursor-pointer group"
      >
        <div className="flex items-center gap-3">
          <span className="w-9 h-9 rounded-xl bg-purple-50 flex items-center justify-center shrink-0">
            <HelpCircle className="w-4 h-4 text-purple-600" />
          </span>
          <div>
            <p className="text-sm font-bold text-gray-900 group-hover:text-purple-700 transition-colors">서비스 이용 가이드 다시 보기</p>
            <p className="text-xs text-gray-500 mt-0.5">야구한입 사용 방법을 처음부터 확인해요.</p>
          </div>
        </div>
        <ChevronRight className="w-4 h-4 text-gray-400 group-hover:text-purple-600 shrink-0" />
      </button>
      <div className="rounded-2xl p-4 bg-gradient-to-r from-purple-50/70 via-indigo-50/40 to-purple-50/70 border border-purple-100/80 text-xs text-purple-900 flex items-start gap-3 shadow-xs">
        <Lightbulb className="w-4 h-4 text-purple-600 shrink-0 mt-0.5" />
        <p className="leading-relaxed"><strong className="font-semibold text-purple-950">야구한입</strong>은 선택한 응원 팀과 자주 찾는 정보를 바탕으로 더 편리한 경기 정보를 제공할 예정이에요.</p>
      </div>
    </div>
  );
}
