<template>
	<header
		class="sticky flex items-center justify-between top-0 z-10 border-b bg-surface-white px-3 py-2.5 sm:px-5"
	>
		<Breadcrumbs :items="breadcrumbs" />
		<Button v-if="canAccess" @click="reloadBatches" :loading="batches.list.loading">
			<template #prefix>
				<RefreshCcw class="h-4 w-4 stroke-1.5" />
			</template>
			{{ __('Refresh') }}
		</Button>
	</header>
	<div class="p-5 pb-10">
		<div v-if="!canAccess" class="max-w-xl mx-auto text-center">
			<EmptyState
				type="Access"
				:title="__('Instructor access required')"
				:message="__('Only assigned instructors or moderators can view grading batches.')"
			/>
		</div>

		<template v-else>
			<div class="mb-6">
				<h1 class="text-2xl font-semibold text-ink-gray-9">
					{{ __('Your teaching batches') }}
				</h1>
				<p class="text-ink-gray-6 mt-1">
					{{ __('Select a batch to open its grading sheet.') }}
				</p>
			</div>

			<div v-if="batches.list.loading" class="grid gap-4">
				<div
					v-for="i in 3"
					:key="i"
					class="h-28 rounded-xl border border-outline-gray-2 bg-surface-gray-1 animate-pulse"
				/>
			</div>

			<div
				v-else-if="batches.data?.length"
				class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4"
			>
				<div
					v-for="batch in batches.data"
					:key="batch.name"
					class="rounded-xl border border-outline-gray-2 bg-surface-white p-4 shadow-sm flex flex-col justify-between"
				>
					<div>
						<div class="text-base font-semibold text-ink-gray-9">
							{{ batch.title || batch.name }}
						</div>
						<div class="text-sm text-ink-gray-5 mt-1">
							{{ __('{0} – {1}')
								.format(
									formatDate(batch.start_date),
									batch.end_date ? formatDate(batch.end_date) : __('Ongoing')
								)
							}}
						</div>
						<div v-if="batch.timezone" class="text-xs text-ink-gray-4 mt-1">
							{{ batch.timezone }}
						</div>
					</div>
					<Button
						variant="solid"
						class="mt-4"
						:loading="openingBatch === batch.name"
						@click="() => openBatch(batch)"
					>
						<template #prefix>
							<NotebookPen class="h-4 w-4 stroke-1.5" />
						</template>
						{{ __('Open grade sheet') }}
					</Button>
				</div>
			</div>

			<EmptyState
				v-else
				type="Batches"
				:title="__('No teaching batches yet')"
				:message="__('Once you are assigned to a batch, it will appear here for grading.')"
			/>
		</template>
	</div>
</template>

<script setup>
import { Breadcrumbs, Button, createListResource, call, usePageMeta } from 'frappe-ui'
import { computed, inject, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { NotebookPen, RefreshCcw } from 'lucide-vue-next'
import { sessionStore } from '@/stores/session'
import EmptyState from '@/components/EmptyState.vue'

const router = useRouter()
const user = inject('$user')
const dayjs = inject('$dayjs')
const openingBatch = ref('')
const { brand } = sessionStore()

const canAccess = computed(() => {
	const data = user.data
	if (!data) return false
	return (
		data.is_instructor ||
		data.is_moderator ||
		data.roles?.includes('Instructor') ||
		data.roles?.includes('LMS Instructor') ||
		data.roles?.includes('Moderator')
	)
})

const batches = createListResource({
	doctype: 'LMS Batch',
	url: 'lms.lms.api.get_batches_for_current_instructor',
	auto: false,
	cache: ['grading-batches', user.data?.name],
})

onMounted(() => {
	if (canAccess.value) {
		reloadBatches()
	}
})

const reloadBatches = () => {
	batches.reload()
}

const formatDate = (date) => {
	if (!date) return __('TBD')
	return dayjs(date).format('MMM DD, YYYY')
}

const openBatch = async (batch) => {
	if (!batch?.name) return
	openingBatch.value = batch.name
	try {
		const sheet = await call('lms.lms.api.get_or_create_grade_sheet', {
			batch_name: batch.name,
		})
		const sheetName = sheet?.name || sheet?.message?.name
		router.push({
			name: 'BatchGrading',
			params: {
				batchName: batch.name,
				sheetName,
			},
		})
	} catch (error) {
		console.error(error)
	} finally {
		openingBatch.value = ''
	}
}

const breadcrumbs = computed(() => [
	{
		label: __('Grading'),
		route: { name: 'Grading' },
	},
])

usePageMeta(() => ({
	title: __('Grading'),
	icon: brand.favicon,
}))
</script>
