<template>
	<header
		class="sticky top-0 z-10 flex items-center justify-between border-b bg-surface-white px-3 py-2.5 sm:px-5"
	>
		<Breadcrumbs v-if="submissionDoc" :items="breadcrumbs" />
		<div v-if="!batchMode" class="space-x-2">
			<Badge
				v-if="submissionDetails.isDirty"
				:label="__('Not Saved')"
				variant="subtle"
				theme="orange"
			/>
			<Button variant="solid" @click="saveSubmission()">
				{{ __('Save') }}
			</Button>
		</div>
	</header>
	<div v-if="submissionDoc" class="w-2/3 border-x mx-auto py-5">
		<div class="text-xl px-10 font-semibold text-ink-gray-9 mb-5">
			{{ submissionDoc.member_name }}
		</div>
		<div class="space-y-4 border-b pb-5 px-10">
			<div class="grid grid-cols-2 gap-5">
				<FormControl
					v-model="submissionDoc.quiz_title"
					:label="__('Quiz')"
					:disabled="true"
				/>
				<FormControl
					v-model="submissionDoc.member_name"
					:label="__('Member')"
					:disabled="true"
				/>
			</div>

			<div class="grid grid-cols-2 gap-5">
				<FormControl
					v-model="submissionDoc.score"
					:label="__('Score')"
					:disabled="true"
				/>
				<FormControl
					v-model="submissionDoc.percentage"
					:label="__('Percentage')"
					:disabled="true"
				/>
			</div>
		</div>

		<div class="divide-y">
			<div
				v-for="(row, index) in submissionDoc.result"
				class="py-5 px-10 space-y-4"
			>
				<div class="text-ink-gray-9">
					<span class="font-semibold"> {{ __('Question') }}: </span>
					<span class="leading-5" v-html="row.question"> </span>
				</div>
				<div class="text-ink-gray-9">
					<span class="font-semibold"> {{ __('Answer') }}: </span>
					<span class="leading-5" v-html="row.answer"></span>
				</div>
				<div class="grid grid-cols-2 gap-5">
					<FormControl
						v-model="row.marks"
						:label="__('Marks')"
						:disabled="batchMode"
					/>
					<FormControl
						v-model="row.marks_out_of"
						:label="__('Marks out of')"
						:disabled="true"
					/>
				</div>
			</div>
		</div>
	</div>
</template>
<script setup>
import {
	createDocumentResource,
	createResource,
	Breadcrumbs,
	FormControl,
	Button,
	Badge,
	usePageMeta,
	toast,
} from 'frappe-ui'
import { computed, onBeforeUnmount, onMounted, inject } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { sessionStore } from '@/stores/session'

const { brand } = sessionStore()
const router = useRouter()
const route = useRoute()
const user = inject('$user')

const batchMode = computed(() => !!route.query.batch)

onMounted(() => {
	const allowed =
		user.data?.is_instructor ||
		user.data?.is_moderator ||
		user.data?.is_evaluator ||
		user.data?.is_system_manager
	if (!allowed) router.push({ name: 'Courses' })

	window.addEventListener('keydown', keyboardShortcut)
})

onBeforeUnmount(() => {
	window.removeEventListener('keydown', keyboardShortcut)
})

const keyboardShortcut = (e) => {
	if (
		e.key === 's' &&
		(e.ctrlKey || e.metaKey) &&
		!e.target.classList.contains('ProseMirror')
	) {
		saveSubmission()
		e.preventDefault()
	}
}

const props = defineProps({
	submission: {
		type: String,
		required: true,
	},
})

const submissionDetails = batchMode.value
	? createResource({
			url: 'lms.lms.utils.get_quiz_submission_details',
			params: {
				submission: props.submission,
			},
			auto: true,
		})
	: createDocumentResource({
			doctype: 'LMS Quiz Submission',
			name: props.submission,
			auto: true,
		})

const submissionDoc = computed(() => {
	return batchMode.value ? submissionDetails.data : submissionDetails.doc
})

const breadcrumbs = computed(() => {
	return [
		{
			label: __('Quiz Submissions'),
			route: {
				name: 'QuizSubmissionList',
				params: {
					quizID: submissionDoc.value.quiz,
				},
				query: route.query,
			},
		},
		{
			label: submissionDoc.value.quiz_title,
		},
	]
})

const saveSubmission = () => {
	if (batchMode.value) return
	submissionDetails.save.submit(
		{},
		{
			onError(err) {
				toast.error(err.messages?.[0] || err)
			},
		}
	)
}

usePageMeta(() => {
	return {
		title: `${submissionDoc.value?.quiz_title}`,
		icon: brand.favicon,
	}
})
</script>
