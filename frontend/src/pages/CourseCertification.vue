<template>
	<header
		class="sticky top-0 z-10 flex items-center justify-between border-b bg-surface-white px-3 py-2.5 sm:px-5"
	>
		<Breadcrumbs class="h-7" :items="breadcrumbs" />
	</header>
	<div class="p-5">
		<div v-if="certificate.data && Object.keys(certificate.data).length">
			<div class="text-lg text-ink-gray-9 font-semibold mb-1">
				{{ __('Certification') }}
			</div>
			<div class="text-ink-gray-9 text-sm">
				{{
					__(
						'You are already certified for this course. Click on the card below to open your certificate.'
					)
				}}
			</div>
			<div
				class="border p-3 w-fit min-w-60 rounded-md space-y-2 hover:bg-surface-gray-1 cursor-pointer mt-5"
				@click="openCertificate(certificate.data)"
			>
				<div class="text-ink-gray-9 font-semibold">
					{{ courseTitle }}
				</div>
				<div
					v-if="certificate.data.serial_number"
					class="text-sm text-ink-gray-7"
				>
					{{ __('Certificate No.') }}: {{ certificate.data.serial_number }}
				</div>
				<a
					v-if="certificate.data.verification_token"
					:href="`/verify/${certificate.data.verification_token}`"
					target="_blank"
					class="text-sm text-ink-blue-3 hover:underline"
					@click.stop
				>
					{{ __('Verify') }}
				</a>
			</div>
		</div>
		<div v-else>
			<UpcomingEvaluations v-if="courses.length" :courses="courses" />
		</div>
	</div>
</template>
<script setup>
import { computed, inject, onMounted, ref } from 'vue'
import { Breadcrumbs, call, createResource, usePageMeta } from 'frappe-ui'
import { useRouter } from 'vue-router'
import { sessionStore } from '../stores/session'
import UpcomingEvaluations from '@/components/UpcomingEvaluations.vue'

const courseTitle = ref(null)
const evaluator = ref(null)
const { brand } = sessionStore()
const courses = ref([])
const user = inject('$user')
const router = useRouter()

const props = defineProps({
	courseName: {
		type: String,
		required: true,
	},
})

onMounted(() => {
	fetchEnrollmentDetails()
	fetchCourseDetails()
})

const certificate = createResource({
	url: 'frappe.client.get_value',
	params: {
		doctype: 'LMS Certificate',
		filters: {
			member: user.data?.name,
			course: props.courseName,
			revoked: 0,
		},
		fieldname: [
			'name',
			'template',
			'serial_number',
			'verification_token',
		],
	},
	cache: [user.data?.name, props.courseName],
})

const fetchEnrollmentDetails = () => {
	call('frappe.client.get_value', {
		doctype: 'LMS Enrollment',
		filters: { member: user.data?.name, course: props.courseName },
		fieldname: ['purchased_certificate'],
	}).then((data) => {
		if (data.purchased_certificate) {
			certificate.reload()
		} else {
			router.push({
				name: 'CourseDetail',
				params: { courseName: props.courseName },
			})
		}
	})
}

const fetchCourseDetails = () => {
	call('frappe.client.get_value', {
		doctype: 'LMS Course',
		filters: { name: props.courseName },
		fieldname: ['title', 'evaluator'],
	}).then((data) => {
		courseTitle.value = data.title
		evaluator.value = data.evaluator
		populateCourses()
	})
}

const populateCourses = () => {
	courses.value = [
		{
			course: props.courseName,
			title: courseTitle.value,
			evaluator: evaluator.value,
		},
	]
}

const openCertificate = (certificate) => {
	window.open(
		`/api/method/frappe.utils.print_format.download_pdf?doctype=LMS+Certificate&name=${
			certificate.name
		}&format=${encodeURIComponent(certificate.template)}&no_letterhead=1`,
		'_blank',
	)
}

const breadcrumbs = computed(() => [
	{
		label: __('Courses'),
		route: { name: 'Courses' },
	},
	{
		label: courseTitle.value,
		route: { name: 'CourseDetail', params: { courseName: props.courseName } },
	},
	{
		label: __('Certification'),
	},
])

usePageMeta(() => {
	return {
		title: courseTitle.value,
		icon: brand.favicon,
	}
})
</script>
