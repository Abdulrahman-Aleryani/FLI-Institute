<template>
	<header
		class="sticky flex items-center justify-between top-0 z-10 border-b bg-surface-white px-3 py-2.5 sm:px-5"
	>
		<Breadcrumbs :items="breadcrumbs" />
		<router-link :to="{ name: 'Batches', query: { certification: true } }">
			<Button>
				<template #prefix>
					<GraduationCap class="h-4 w-4 stroke-1.5" />
				</template>
				{{ __('Get Certified') }}
			</Button>
		</router-link>
	</header>
	<div class="mx-auto w-full max-w-4xl pt-6 pb-10">
		<div
			v-if="canViewDirectory"
			class="flex flex-col md:flex-row justify-between mb-4 px-3"
		>
			<div class="text-xl font-semibold text-ink-gray-7 mb-4 md:mb-0">
				{{ memberCount }} {{ __('certified members') }}
			</div>
			<div class="grid grid-cols-2 gap-2">
				<FormControl
					v-model="nameFilter"
					:placeholder="__('Search by Name')"
					type="text"
					class="min-w-40 lg:min-w-0 lg:w-32 xl:w-40"
					@input="updateParticipants()"
				/>
				<div
					v-if="categories.data?.length"
					class="min-w-40 lg:min-w-0 lg:w-32 xl:w-40"
				>
					<Select
						v-model="currentCategory"
						:options="categories.data"
						:placeholder="__('Category')"
						@change="updateParticipants()"
					/>
				</div>
			</div>
		</div>
		<template v-if="canViewDirectory">
			<div v-if="participants.data?.length" class="divide-y">
				<template v-for="participant in participants.data">
					<router-link
						:to="{
							name: 'ProfileCertificates',
							params: {
								username: participant.username,
							},
						}"
						class="flex sm:rounded px-3 py-2 sm:h-15 hover:bg-surface-gray-2"
					>
						<div class="flex items-center w-full space-x-3">
							<Avatar
								:image="participant.user_image"
								class="size-8 rounded-full object-contain"
								:label="participant.full_name"
								size="2xl"
							/>
							<div class="flex flex-col md:flex-row w-full">
								<div class="flex-1">
									<div class="text-base font-medium text-ink-gray-8">
										{{ participant.full_name }}
									</div>
									<div
										v-if="participant.headline"
										class="mt-1.5 text-base text-ink-gray-5"
									>
										{{ participant.headline }}
									</div>
								</div>
								<div
									class="flex items-center space-x-3 md:space-x-24 text-sm md:text-base mt-1.5"
								>
									<div class="text-ink-gray-5">
										{{ participant.certificate_count }}
										{{
											participant.certificate_count > 1
												? __('certificates')
												: __('certificate')
										}}
									</div>
								</div>
							</div>
						</div>
					</router-link>
				</template>
			</div>
			<EmptyState v-else type="Certified Members" />
			<div
				v-if="!participants.list.loading && participants.hasNextPage"
				class="flex justify-center mt-5"
			>
				<Button @click="participants.next()">
					{{ __('Load More') }}
				</Button>
			</div>
		</template>
		<template v-else>
			<div
				v-if="myCertificates.data?.length"
				class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 px-3"
			>
				<div
					v-for="certificate in myCertificates.data"
					:key="certificate.name"
					class="flex flex-col bg-surface-white border rounded-lg p-3 cursor-pointer hover:bg-surface-menu-bar"
					@click="openCertificate(certificate)"
				>
					<div class="font-medium leading-5 mb-2 text-ink-gray-9">
						{{ certificate.course_title || certificate.batch_title }}
					</div>
					<div
						v-if="certificate.serial_number"
						class="text-xs text-ink-gray-5 mt-1"
					>
						{{ __('Certificate No.') }}: {{ certificate.serial_number }}
					</div>
					<div class="flex items-center space-x-2 mt-2">
						<Badge v-if="certificate.revoked" theme="red">
							{{ __('Revoked') }}
						</Badge>
						<a
							v-if="certificate.verification_token"
							:href="`/verify/${certificate.verification_token}`"
							target="_blank"
							class="text-xs text-ink-blue-3 hover:underline"
							@click.stop
						>
							{{ __('Verify') }}
						</a>
					</div>
				</div>
			</div>
			<EmptyState v-else type="Certificates" />
		</template>
	</div>
</template>
<script setup>
import {
	Avatar,
	Badge,
	Breadcrumbs,
	Button,
	call,
	createListResource,
	createResource,
	FormControl,
	Select,
	usePageMeta,
} from 'frappe-ui'
import { computed, onMounted, ref } from 'vue'
import { GraduationCap } from 'lucide-vue-next'
import { sessionStore } from '../stores/session'
import { usersStore } from '../stores/user'
import EmptyState from '@/components/EmptyState.vue'

const currentCategory = ref('')
const filters = ref({})
const nameFilter = ref('')
const { brand } = sessionStore()
const { userResource } = usersStore()
const memberCount = ref(0)

const canViewDirectory = computed(() => {
	const data = userResource.data
	return (
		data?.is_moderator ||
		data?.is_instructor ||
		data?.is_evaluator ||
		data?.is_system_manager ||
		data?.roles?.includes('Administrator')
	)
})

onMounted(() => {
	setFiltersFromQuery()
	updateParticipants()
})

const myCertificates = createResource({
	url: 'lms.lms.api.get_my_certificates',
	auto: true,
})

const openCertificate = (certificate) => {
	window.open(
		`/api/method/frappe.utils.print_format.download_pdf?doctype=LMS+Certificate&name=${
			certificate.name
		}&format=${encodeURIComponent(certificate.template)}&no_letterhead=1`,
	)
}

const participants = createListResource({
	doctype: 'LMS Certificate',
	url: 'lms.lms.api.get_certified_participants',
	start: 0,
	cache: ['certified_participants'],
	pageLength: 100,
})

const getMemberCount = () => {
	call('lms.lms.api.get_count_of_certified_members', {
		filters: filters.value,
	}).then((data) => {
		memberCount.value = data
	})
}

const categories = createListResource({
	doctype: 'LMS Certificate',
	url: 'lms.lms.api.get_certification_categories',
	cache: ['certification_categories'],
	auto: true,
	transform(data) {
		data.unshift({ label: __(''), value: '' })
		return data
	},
})

const updateParticipants = () => {
	updateFilters()
	getMemberCount()
	setQueryParams()

	participants.update({
		filters: filters.value,
	})
	participants.reload()
}

const updateFilters = () => {
	if (currentCategory.value) {
		filters.value.category = currentCategory.value
	} else {
		delete filters.value.category
	}

	if (nameFilter.value) {
		filters.value.member_name = ['like', `%${nameFilter.value}%`]
	} else {
		delete filters.value.member_name
	}
}

const setQueryParams = () => {
	let queries = new URLSearchParams(location.search)
	let filterKeys = {
		category: currentCategory.value,
		name: nameFilter.value,
	}

	Object.keys(filterKeys).forEach((key) => {
		if (filterKeys[key]) {
			queries.set(key, filterKeys[key])
		} else {
			queries.delete(key)
		}
	})
	history.replaceState(
		{},
		'',
		`${location.pathname}${queries.size > 0 ? `?${queries.toString()}` : ''}`
	)
}

const setFiltersFromQuery = () => {
	let queries = new URLSearchParams(location.search)
	nameFilter.value = queries.get('name') || ''
	currentCategory.value = queries.get('category') || ''
}

const pageTitle = computed(() =>
	canViewDirectory.value ? __('Certified Members') : __('My Certificates'),
)

const breadcrumbs = computed(() => [
	{
		label: pageTitle.value,
		route: { name: 'CertifiedParticipants' },
	},
])

usePageMeta(() => {
	return {
		title: pageTitle.value,
		icon: brand.favicon,
	}
})
</script>
<style>
.headline {
	display: -webkit-box;
	-webkit-line-clamp: 1;
	-webkit-box-orient: vertical;
	text-overflow: ellipsis;
	width: 100%;
	overflow: hidden;
}
</style>
