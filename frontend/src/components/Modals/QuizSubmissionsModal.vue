<template>
	<Dialog
		v-model="show"
		:options="{
			title: __('Check Submissions'),
			size: 'md',
		}"
	>
		<template #body-content>
			<div
				v-if="quizzes.loading"
				class="text-sm text-ink-gray-5 text-center py-5"
			>
				{{ __('Loading...') }}
			</div>
			<div v-else-if="quizzes.data?.length" class="divide-y max-h-96 overflow-y-auto">
				<button
					v-for="quiz in quizzes.data"
					:key="quiz.name"
					class="w-full text-left px-2 py-3 rounded hover:bg-surface-gray-2"
					@click="openSubmissions(quiz)"
				>
					<div class="text-ink-gray-9 font-medium">
						{{ quiz.title || quiz.quiz }}
					</div>
					<div class="text-xs text-ink-gray-5">
						{{ quiz.quiz }}
					</div>
				</button>
			</div>
			<div v-else class="text-sm italic text-ink-gray-5">
				{{ __('No quizzes assigned to this batch.') }}
			</div>
		</template>
	</Dialog>
</template>
<script setup>
import { Dialog, createResource } from 'frappe-ui'
import { useRouter } from 'vue-router'
import { watch } from 'vue'

const show = defineModel()
const router = useRouter()

const props = defineProps({
	batch: {
		type: String,
		required: true,
	},
})

const quizzes = createResource({
	url: 'lms.lms.utils.get_batch_quizzes',
	makeParams() {
		return {
			batch: props.batch,
		}
	},
})

watch(show, (value) => {
	if (value) quizzes.fetch()
})

const openSubmissions = (quiz) => {
	show.value = false
	router.push({
		name: 'QuizSubmissionList',
		params: {
			quizID: quiz.quiz,
		},
		query: {
			batch: props.batch,
		},
	})
}
</script>
