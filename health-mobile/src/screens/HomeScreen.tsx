import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';
import { useAuthStore } from '../store/authStore';

const MENU_ITEMS = [
  { label: '운동 & 식단 기록', emoji: '🏋️', screen: 'Health' },
  { label: '맞춤 추천', emoji: '🥗', screen: 'Recommendation' },
  { label: '건강 게시판', emoji: '📰', screen: 'Board' },
];

export default function HomeScreen({ navigation }: any) {
  const { user } = useAuthStore();

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <View style={styles.header}>
        <Text style={styles.greeting}>안녕하세요, {user?.nickname}님 👋</Text>
        <Text style={styles.sub}>오늘도 건강한 하루 되세요!</Text>
      </View>

      <View style={styles.grid}>
        {MENU_ITEMS.map((item) => (
          <TouchableOpacity
            key={item.screen}
            style={styles.card}
            onPress={() => navigation.navigate(item.screen)}
          >
            <Text style={styles.emoji}>{item.emoji}</Text>
            <Text style={styles.cardLabel}>{item.label}</Text>
          </TouchableOpacity>
        ))}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F9FAFB' },
  content: { padding: 20 },
  header: { marginBottom: 28 },
  greeting: { fontSize: 22, fontWeight: '700', color: '#111827' },
  sub: { fontSize: 14, color: '#6B7280', marginTop: 4 },
  grid: { flexDirection: 'row', flexWrap: 'wrap', gap: 12 },
  card: {
    backgroundColor: '#fff', borderRadius: 16, padding: 20,
    width: '47%', alignItems: 'center',
    shadowColor: '#000', shadowOpacity: 0.06, shadowRadius: 8, elevation: 2,
    minHeight: 110, justifyContent: 'center',
  },
  emoji: { fontSize: 32, marginBottom: 8 },
  cardLabel: { fontSize: 13, fontWeight: '600', color: '#374151', textAlign: 'center' },
});
