import { useState } from 'react';
import {
  View, Text, FlatList, TouchableOpacity, Modal, TextInput,
  StyleSheet, ActivityIndicator, Alert, KeyboardAvoidingView,
  Platform, ScrollView,
} from 'react-native';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { healthApi } from '../services/api';
import type { ExerciseLog, DietLog, WeightRecord } from '../types';

type Tab = 'exercise' | 'diet' | 'weight';

const TABS: { key: Tab; label: string }[] = [
  { key: 'exercise', label: '운동일지' },
  { key: 'diet', label: '식단일지' },
  { key: 'weight', label: '체중' },
];

const MEAL_LABELS: Record<string, string> = {
  breakfast: '아침', lunch: '점심', dinner: '저녁', snack: '간식',
};
const MEAL_TYPES = ['breakfast', 'lunch', 'dinner', 'snack'] as const;
type MealType = typeof MEAL_TYPES[number];

function todayStr() {
  return new Date().toISOString().split('T')[0];
}

// ── Shared helpers ───────────────────────────────────

function FieldLabel({ children }: { children: string }) {
  return <Text style={s.fieldLabel}>{children}</Text>;
}

function EmptyState({ label }: { label: string }) {
  return (
    <View style={s.empty}>
      <Text style={s.emptyText}>{label}</Text>
      <Text style={s.emptyHint}>+ 버튼으로 추가하세요</Text>
    </View>
  );
}

function Fab({ onPress }: { onPress: () => void }) {
  return (
    <TouchableOpacity style={s.fab} onPress={onPress} activeOpacity={0.85}>
      <Text style={s.fabIcon}>+</Text>
    </TouchableOpacity>
  );
}

// ── Exercise Tab ─────────────────────────────────────

function ExerciseTab() {
  const qc = useQueryClient();
  const [modal, setModal] = useState(false);
  const [date, setDate] = useState(todayStr());
  const [content, setContent] = useState('');
  const [duration, setDuration] = useState('');
  const [exName, setExName] = useState('');
  const [sets, setSets] = useState('');
  const [reps, setReps] = useState('');
  const [weight, setWeight] = useState('');

  const { data, isLoading } = useQuery({
    queryKey: ['exercise-logs'],
    queryFn: () => healthApi.getExerciseLogs().then(r => r.data as ExerciseLog[]),
  });

  const { mutate, isPending } = useMutation({
    mutationFn: (payload: object) => healthApi.createExerciseLog(payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['exercise-logs'] });
      closeModal();
    },
    onError: () => Alert.alert('오류', '저장에 실패했습니다.'),
  });

  function closeModal() {
    setModal(false);
    setDate(todayStr()); setContent(''); setDuration('');
    setExName(''); setSets(''); setReps(''); setWeight('');
  }

  function submit() {
    if (!exName.trim()) { Alert.alert('운동 이름을 입력하세요.'); return; }
    mutate({
      date,
      content,
      duration_minutes: parseInt(duration) || 30,
      exercises: [{
        name: exName,
        sets: sets ? parseInt(sets) : undefined,
        reps: reps ? parseInt(reps) : undefined,
        weight: weight ? parseFloat(weight) : undefined,
      }],
    });
  }

  if (isLoading) return <ActivityIndicator style={{ flex: 1 }} color="#2563EB" />;

  return (
    <View style={{ flex: 1 }}>
      <FlatList
        data={data ?? []}
        keyExtractor={item => String(item.id)}
        contentContainerStyle={s.listContent}
        ListEmptyComponent={<EmptyState label="운동 기록이 없습니다" />}
        renderItem={({ item }) => (
          <View style={s.card}>
            <View style={s.cardHeader}>
              <Text style={s.cardDate}>{item.date}</Text>
              <Text style={s.cardMeta}>{item.duration_minutes}분</Text>
            </View>
            {item.exercises?.map((ex, i) => (
              <Text key={i} style={s.cardDetail}>
                {ex.name}
                {ex.sets ? ` ${ex.sets}세트` : ''}
                {ex.reps ? ` × ${ex.reps}회` : ''}
                {ex.weight ? ` (${ex.weight}kg)` : ''}
              </Text>
            ))}
            {!!item.content && <Text style={s.cardNote}>{item.content}</Text>}
          </View>
        )}
      />
      <Fab onPress={() => setModal(true)} />

      <Modal visible={modal} animationType="slide" presentationStyle="pageSheet">
        <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : undefined} style={{ flex: 1 }}>
          <ScrollView style={s.modal} keyboardShouldPersistTaps="handled">
            <View style={s.modalHeader}>
              <Text style={s.modalTitle}>운동 기록 추가</Text>
              <TouchableOpacity onPress={closeModal}>
                <Text style={s.modalClose}>닫기</Text>
              </TouchableOpacity>
            </View>

            <FieldLabel>날짜</FieldLabel>
            <TextInput style={s.input} value={date} onChangeText={setDate} placeholder="YYYY-MM-DD" />

            <FieldLabel>운동 시간 (분)</FieldLabel>
            <TextInput style={s.input} value={duration} onChangeText={setDuration} keyboardType="numeric" placeholder="30" />

            <FieldLabel>운동 이름 *</FieldLabel>
            <TextInput style={s.input} value={exName} onChangeText={setExName} placeholder="벤치프레스" />

            <View style={s.row3}>
              <View style={{ flex: 1 }}>
                <FieldLabel>세트</FieldLabel>
                <TextInput style={s.input} value={sets} onChangeText={setSets} keyboardType="numeric" placeholder="3" />
              </View>
              <View style={{ flex: 1, marginLeft: 8 }}>
                <FieldLabel>횟수</FieldLabel>
                <TextInput style={s.input} value={reps} onChangeText={setReps} keyboardType="numeric" placeholder="10" />
              </View>
              <View style={{ flex: 1, marginLeft: 8 }}>
                <FieldLabel>무게(kg)</FieldLabel>
                <TextInput style={s.input} value={weight} onChangeText={setWeight} keyboardType="decimal-pad" placeholder="60" />
              </View>
            </View>

            <FieldLabel>메모</FieldLabel>
            <TextInput
              style={[s.input, { height: 80, textAlignVertical: 'top' }]}
              value={content} onChangeText={setContent}
              multiline placeholder="오늘의 운동 메모..."
            />

            <TouchableOpacity style={[s.btn, isPending && s.btnDisabled]} onPress={submit} disabled={isPending}>
              <Text style={s.btnText}>{isPending ? '저장 중...' : '저장'}</Text>
            </TouchableOpacity>
          </ScrollView>
        </KeyboardAvoidingView>
      </Modal>
    </View>
  );
}

// ── Diet Tab ─────────────────────────────────────────

function DietTab() {
  const qc = useQueryClient();
  const [modal, setModal] = useState(false);
  const [date, setDate] = useState(todayStr());
  const [mealType, setMealType] = useState<MealType>('breakfast');
  const [foodName, setFoodName] = useState('');
  const [calories, setCalories] = useState('');
  const [amount, setAmount] = useState('');

  const { data, isLoading } = useQuery({
    queryKey: ['diet-logs'],
    queryFn: () => healthApi.getDietLogs().then(r => r.data as DietLog[]),
  });

  const { mutate, isPending } = useMutation({
    mutationFn: (payload: object) => healthApi.createDietLog(payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['diet-logs'] });
      closeModal();
    },
    onError: () => Alert.alert('오류', '저장에 실패했습니다.'),
  });

  function closeModal() {
    setModal(false);
    setDate(todayStr()); setMealType('breakfast');
    setFoodName(''); setCalories(''); setAmount('');
  }

  function submit() {
    if (!foodName.trim()) { Alert.alert('음식 이름을 입력하세요.'); return; }
    const cal = parseInt(calories) || 0;
    mutate({
      date,
      meals: [{
        meal_type: mealType,
        foods: [{ name: foodName, calories: cal, amount: amount || undefined }],
      }],
      total_calories: cal,
    });
  }

  if (isLoading) return <ActivityIndicator style={{ flex: 1 }} color="#2563EB" />;

  return (
    <View style={{ flex: 1 }}>
      <FlatList
        data={data ?? []}
        keyExtractor={item => String(item.id)}
        contentContainerStyle={s.listContent}
        ListEmptyComponent={<EmptyState label="식단 기록이 없습니다" />}
        renderItem={({ item }) => (
          <View style={s.card}>
            <View style={s.cardHeader}>
              <Text style={s.cardDate}>{item.date}</Text>
              <Text style={s.cardMeta}>{item.total_calories} kcal</Text>
            </View>
            {item.meals?.flatMap((m, mi) =>
              m.foods?.map((f, fi) => (
                <Text key={`${mi}-${fi}`} style={s.cardDetail}>
                  [{MEAL_LABELS[m.meal_type]}] {f.name}
                  {f.amount ? ` (${f.amount})` : ''} — {f.calories}kcal
                </Text>
              ))
            )}
          </View>
        )}
      />
      <Fab onPress={() => setModal(true)} />

      <Modal visible={modal} animationType="slide" presentationStyle="pageSheet">
        <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : undefined} style={{ flex: 1 }}>
          <ScrollView style={s.modal} keyboardShouldPersistTaps="handled">
            <View style={s.modalHeader}>
              <Text style={s.modalTitle}>식단 기록 추가</Text>
              <TouchableOpacity onPress={closeModal}>
                <Text style={s.modalClose}>닫기</Text>
              </TouchableOpacity>
            </View>

            <FieldLabel>날짜</FieldLabel>
            <TextInput style={s.input} value={date} onChangeText={setDate} placeholder="YYYY-MM-DD" />

            <FieldLabel>식사 종류</FieldLabel>
            <View style={s.mealRow}>
              {MEAL_TYPES.map(type => (
                <TouchableOpacity
                  key={type}
                  style={[s.mealChip, mealType === type && s.mealChipActive]}
                  onPress={() => setMealType(type)}
                >
                  <Text style={[s.mealChipText, mealType === type && s.mealChipTextActive]}>
                    {MEAL_LABELS[type]}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>

            <FieldLabel>음식 이름 *</FieldLabel>
            <TextInput style={s.input} value={foodName} onChangeText={setFoodName} placeholder="김치찌개" />

            <View style={s.row3}>
              <View style={{ flex: 1 }}>
                <FieldLabel>칼로리 (kcal)</FieldLabel>
                <TextInput style={s.input} value={calories} onChangeText={setCalories} keyboardType="numeric" placeholder="500" />
              </View>
              <View style={{ flex: 1, marginLeft: 8 }}>
                <FieldLabel>양</FieldLabel>
                <TextInput style={s.input} value={amount} onChangeText={setAmount} placeholder="1인분" />
              </View>
            </View>

            <TouchableOpacity style={[s.btn, isPending && s.btnDisabled]} onPress={submit} disabled={isPending}>
              <Text style={s.btnText}>{isPending ? '저장 중...' : '저장'}</Text>
            </TouchableOpacity>
          </ScrollView>
        </KeyboardAvoidingView>
      </Modal>
    </View>
  );
}

// ── Weight Tab ───────────────────────────────────────

function WeightTab() {
  const qc = useQueryClient();
  const [modal, setModal] = useState(false);
  const [date, setDate] = useState(todayStr());
  const [weightVal, setWeightVal] = useState('');

  const { data, isLoading } = useQuery({
    queryKey: ['weight-records'],
    queryFn: () => healthApi.getWeightRecords().then(r => r.data as WeightRecord[]),
  });

  const { mutate, isPending } = useMutation({
    mutationFn: (payload: { date: string; weight: number }) => healthApi.addWeightRecord(payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['weight-records'] });
      setModal(false);
      setDate(todayStr()); setWeightVal('');
    },
    onError: () => Alert.alert('오류', '저장에 실패했습니다.'),
  });

  function submit() {
    const w = parseFloat(weightVal);
    if (!w) { Alert.alert('체중을 입력하세요.'); return; }
    mutate({ date, weight: w });
  }

  if (isLoading) return <ActivityIndicator style={{ flex: 1 }} color="#2563EB" />;

  return (
    <View style={{ flex: 1 }}>
      <FlatList
        data={data ?? []}
        keyExtractor={item => String(item.id)}
        contentContainerStyle={s.listContent}
        ListEmptyComponent={<EmptyState label="체중 기록이 없습니다" />}
        renderItem={({ item }) => (
          <View style={[s.card, s.weightCard]}>
            <Text style={s.cardDate}>{item.date}</Text>
            <Text style={s.weightNum}>
              {item.weight}<Text style={s.weightUnit}> kg</Text>
            </Text>
          </View>
        )}
      />
      <Fab onPress={() => setModal(true)} />

      <Modal visible={modal} animationType="slide" presentationStyle="pageSheet">
        <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : undefined} style={{ flex: 1 }}>
          <View style={s.modal}>
            <View style={s.modalHeader}>
              <Text style={s.modalTitle}>체중 기록</Text>
              <TouchableOpacity onPress={() => setModal(false)}>
                <Text style={s.modalClose}>닫기</Text>
              </TouchableOpacity>
            </View>

            <FieldLabel>날짜</FieldLabel>
            <TextInput style={s.input} value={date} onChangeText={setDate} placeholder="YYYY-MM-DD" />

            <FieldLabel>체중 (kg)</FieldLabel>
            <TextInput style={s.input} value={weightVal} onChangeText={setWeightVal} keyboardType="decimal-pad" placeholder="70.5" />

            <TouchableOpacity style={[s.btn, isPending && s.btnDisabled]} onPress={submit} disabled={isPending}>
              <Text style={s.btnText}>{isPending ? '저장 중...' : '저장'}</Text>
            </TouchableOpacity>
          </View>
        </KeyboardAvoidingView>
      </Modal>
    </View>
  );
}

// ── Root ─────────────────────────────────────────────

export default function HealthScreen() {
  const [activeTab, setActiveTab] = useState<Tab>('exercise');

  return (
    <View style={s.container}>
      <View style={s.tabBar}>
        {TABS.map(tab => (
          <TouchableOpacity
            key={tab.key}
            style={[s.tabBtn, activeTab === tab.key && s.tabBtnActive]}
            onPress={() => setActiveTab(tab.key)}
          >
            <Text style={[s.tabLabel, activeTab === tab.key && s.tabLabelActive]}>
              {tab.label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {activeTab === 'exercise' && <ExerciseTab />}
      {activeTab === 'diet' && <DietTab />}
      {activeTab === 'weight' && <WeightTab />}
    </View>
  );
}

// ── Styles ───────────────────────────────────────────

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F9FAFB' },

  // Tab bar
  tabBar: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  tabBtn: {
    flex: 1, paddingVertical: 14, alignItems: 'center',
    borderBottomWidth: 2, borderBottomColor: 'transparent',
  },
  tabBtnActive: { borderBottomColor: '#2563EB' },
  tabLabel: { fontSize: 14, fontWeight: '500', color: '#6B7280' },
  tabLabelActive: { color: '#2563EB', fontWeight: '700' },

  // List
  listContent: { padding: 16, gap: 12, flexGrow: 1 },

  // Card
  card: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    shadowColor: '#000',
    shadowOpacity: 0.05,
    shadowRadius: 6,
    elevation: 2,
  },
  cardHeader: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 8 },
  cardDate: { fontSize: 14, fontWeight: '700', color: '#111827' },
  cardMeta: { fontSize: 13, color: '#2563EB', fontWeight: '600' },
  cardDetail: { fontSize: 13, color: '#374151', marginTop: 4 },
  cardNote: { fontSize: 12, color: '#9CA3AF', marginTop: 6 },

  // Weight card
  weightCard: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  weightNum: { fontSize: 22, fontWeight: '800', color: '#111827' },
  weightUnit: { fontSize: 14, fontWeight: '400', color: '#6B7280' },

  // Empty
  empty: { flex: 1, alignItems: 'center', justifyContent: 'center', paddingVertical: 80 },
  emptyText: { fontSize: 15, color: '#9CA3AF', fontWeight: '500' },
  emptyHint: { fontSize: 12, color: '#D1D5DB', marginTop: 6 },

  // FAB
  fab: {
    position: 'absolute', bottom: 24, right: 20,
    width: 52, height: 52, borderRadius: 26,
    backgroundColor: '#2563EB', alignItems: 'center', justifyContent: 'center',
    shadowColor: '#2563EB', shadowOpacity: 0.4, shadowRadius: 8, elevation: 5,
  },
  fabIcon: { fontSize: 28, color: '#fff', lineHeight: 32 },

  // Modal
  modal: { flex: 1, backgroundColor: '#fff', padding: 20 },
  modalHeader: {
    flexDirection: 'row', justifyContent: 'space-between',
    alignItems: 'center', marginBottom: 24,
    paddingTop: Platform.OS === 'ios' ? 8 : 0,
  },
  modalTitle: { fontSize: 18, fontWeight: '700', color: '#111827' },
  modalClose: { fontSize: 14, color: '#6B7280' },

  // Form
  fieldLabel: { fontSize: 12, fontWeight: '600', color: '#374151', marginBottom: 6, marginTop: 14 },
  input: {
    borderWidth: 1, borderColor: '#E5E7EB', borderRadius: 8,
    paddingHorizontal: 12, paddingVertical: 10,
    fontSize: 14, color: '#111827', backgroundColor: '#F9FAFB',
  },
  row3: { flexDirection: 'row', marginTop: 0 },

  // Meal chips
  mealRow: { flexDirection: 'row', gap: 8, flexWrap: 'wrap' },
  mealChip: {
    paddingHorizontal: 14, paddingVertical: 7,
    borderRadius: 20, borderWidth: 1, borderColor: '#E5E7EB',
    backgroundColor: '#F9FAFB',
  },
  mealChipActive: { backgroundColor: '#2563EB', borderColor: '#2563EB' },
  mealChipText: { fontSize: 13, color: '#6B7280', fontWeight: '500' },
  mealChipTextActive: { color: '#fff', fontWeight: '700' },

  // Button
  btn: {
    backgroundColor: '#2563EB', borderRadius: 10,
    paddingVertical: 14, alignItems: 'center', marginTop: 28, marginBottom: 40,
  },
  btnDisabled: { opacity: 0.6 },
  btnText: { color: '#fff', fontSize: 15, fontWeight: '700' },
});
