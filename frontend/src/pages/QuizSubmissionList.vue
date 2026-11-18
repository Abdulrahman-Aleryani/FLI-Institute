<template>
	<header
		class="sticky top-0 z-10 flex items-center justify-between border-b bg-surface-white px-3 py-2.5 sm:px-5"
	>
		<Breadcrumbs :items="breadcrumbs" />
	</header>
	<div v-if="rows.length" class="md:w-3/4 md:mx-auto py-5 mx-5">
		<div class="text-xl font-semibold mb-5 text-ink-gray-9">
			{{ rows[0].quiz_title }}
		</div>
		<ListView
			:columns="quizColumns"
			:rows="rows"
			row-key="name"
			:options="{ showTooltip: false, selectable: false }"
		>
			<ListHeader
				class="mb-2 grid items-center space-x-4 rounded bg-surface-gray-2 p-2"
			>
				<ListHeaderItem :item="item" v-for="item in quizColumns">
				</ListHeaderItem>
			</ListHeader>
			<ListRows>
				<router-link
					v-for="row in rows"
					:to="{
						name: 'QuizSubmission',
						params: {
							submission: row.name,
						},
						query: route.query,
					}"
				>
					<ListRow :row="row" />
				</router-link>
			</ListRows>
		</ListView>
		<div class="flex justify-center my-5">
			<Button v-if="!batch && submissions.hasNextPage" @click="submissions.next()">
				{{ __('Load More') }}
			</Button>
		</div>
	</div>
	<EmptyState v-else type="Quiz Submissions" />
</template>
<script setup>
import {
	createListResource,
	createResource,
	Breadcrumbs,
	Button,
	ListView,
	ListRow,
	ListRows,
	ListHeader,
	ListHeaderItem,
	usePageMeta,
} from 'frappe-ui'
import { computed, onMounted, inject } from 'vue'
import { sessionStore } from '../stores/session'
import { useRoute, useRouter } from 'vue-router'
import EmptyState from '@/components/EmptyState.vue'
import dayjs from '@/utils/dayjs'

const { brand } = sessionStore()
const router = useRouter()
const route = useRoute()
const user = inject('$user')

const batch = computed(() => route.query.batch || null)

onMounted(() => {
	const allowed =
		user.data?.is_instructor ||
		user.data?.is_moderator ||
		user.data?.is_evaluator ||
		user.data?.is_system_manager
	if (!allowed) router.push({ name: 'Courses' })
})

const props = defineProps({
	quizID: {
		type: String,
		required: true,
	},
})

const submissions = createListResource({
	doctype: 'LMS Quiz Submission',
	filters: {
		quiz: props.quizID,
	},
	fields: ['name', 'member_name', 'score', 'percentage', 'quiz_title'],
	orderBy: 'creation desc',
	auto: !batch.value,
})

const batchSubmissions = createResource({
	url: 'lms.lms.utils.get_batch_quiz_submissions',
	params: {
		quiz: props.quizID,
		batch: batch.value,
	},
	auto: !!batch.value,
})

const rows = computed(() => {
	const data = (batch.value ? batchSubmissions.data : submissions.data) || []
	if (!batch.value) return data

	const attempts = {}
	return data.map((row) => {
		attempts[row.member] = (attempts[row.member] || 0) + 1
		return {
			...row,
			attempt: attempts[row.member],
			submitted_on: dayjs(row.creation).format('DD MMM YYYY, hh:mm A'),
		}
	})
})

const quizColumns = computed(() => {
	let columns = [
		{
			label: __('Member'),
			key: 'member_name',
			width: 1,
		},
		{
			label: __('Score'),
			key: 'score',
			width: 1,
			align: 'center',
		},
		{
			label: __('Percentage'),
			key: 'percentage',
			width: 1,
			align: 'center',
		},
	]

	if (batch.value) {
		columns.push(
			{
				label: __('Attempt'),
				key: 'attempt',
				width: 1,
				align: 'center',
			},
			{
				label: __('Submitted On'),
				key: 'submitted_on',
				width: 2,
			}
		)
	}
	return columns
})

const breadcrumbs = computed(() => {
	let crumbs = []
	if (batch.value) {
		crumbs.push({
			label: batch.value,
			route: {
				name: 'Batch',
				params: {
					batchName: batch.value,
				},
			},
		})
	}
	crumbs.push({ label: __('Quiz Submissions') })
	return crumbs
})

usePageMeta(() => {
	return {
		title: __('Quiz Submissions'),
		icon: brand.favicon,
	}
})
</script>
